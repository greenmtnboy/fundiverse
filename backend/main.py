from typing import List, Dict, Annotated, Callable, Any, Optional
import dotenv

dotenv.load_dotenv()
import os
import sys
import multiprocessing
import uvicorn
import uuid
from enum import Enum
from datetime import datetime, timedelta
from uvicorn.config import LOGGING_CONFIG
from fastapi import (
    APIRouter,
    FastAPI,
    HTTPException,
    Depends,
    status,
    BackgroundTasks,
    Body,
    Request,
)
from contextlib import asynccontextmanager
from fastapi.routing import APIRoute
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dataclasses import dataclass, field
from pytz import UTC
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import get_type_hints
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field, ConfigDict
from pydantic.alias_generators import to_camel
from collections import defaultdict

from copy import deepcopy


from fastapi.responses import PlainTextResponse
from starlette.background import BackgroundTask
import asyncio
import traceback
from logging import getLogger, StreamHandler
from py_portfolio_index.exceptions import OrderError, ExtraAuthenticationStepException
from py_portfolio_index.portfolio_providers.base_portfolio import BaseProvider
from py_portfolio_index.portfolio_providers.helpers.robinhood import (
    login as rh_login,
)
from py_portfolio_index.portfolio_providers.helpers.schwab import (
    SchwabAuthContext,
    create_login_context,
    fetch_response,
)
from py_portfolio_index.models import (
    CompositePortfolio,
    RealPortfolio,
    LoginResponse,
    RealPortfolioElement,
    Money,
    OrderType,
    OrderElement,
    ProfitModel,
    IdealPortfolio,
)

from py_portfolio_index import (
    INDEXES,
    STOCK_LISTS,
    AlpacaProvider,
    PaperAlpacaProvider,
    RobinhoodProvider,
    WebullProvider,
    WebullPaperProvider,
    SchwabProvider,
    PurchaseStrategy,
    generate_composite_order_plan,
    AVAILABLE_PROVIDERS,
    Logger,
)
from py_portfolio_index.models import OrderPlan
from py_portfolio_index.exceptions import ConfigurationError
from py_portfolio_index.enums import ProviderType


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

SERVE_PORT = 3042

logger = getLogger(__name__)
# hook into py-portfolio-index-logger
Logger.addHandler(StreamHandler())


class ShutdownException(Exception):
    pass


class SchwabExtraAuthenticationStepException(Exception):
    def __init__(self, response: SchwabAuthContext, *args):
        super().__init__(*args)
        self.response = response


class SubPortfolioRefreshException(Exception):
    def __init__(self, provider: ProviderType, error: Exception):
        self.error = error
        self.provider = provider


class BackgroundStatus(Enum):
    RUNNING = 1
    SUCCESS = 2
    FAILED = -1


@dataclass
class AsyncTask:
    guid: str
    status: BackgroundStatus
    started: datetime
    result: Any
    error: Exception | None = None


@dataclass
class ActiveConfig:
    logged_in: str | None = None
    provider_cache: Dict[ProviderType, BaseProvider] = field(default_factory=dict)
    holding_cache: Dict[ProviderType, RealPortfolio] = field(default_factory=dict)
    pending_auth_response: LoginResponse | None = None
    pending_schwab_response: SchwabAuthContext | None = None
    auth_token: str | None = None
    validate: bool = False
    background_tasks: Dict[str, AsyncTask] = field(default_factory=dict)

    @property
    def default_provider(self):
        # get the fastest provider
        priority = [
            ProviderType.ALPACA,
            ProviderType.ROBINHOOD,
            ProviderType.WEBULL,
            ProviderType.SCHWAB,
            ProviderType.ALPACA_PAPER,
            ProviderType.WEBULL_PAPER,
        ]
        for provider in priority:
            for key, _ in self.provider_cache.items():
                if key == provider:
                    return key
        if self.provider_cache:
            return list(self.provider_cache.keys())[0]
        raise HTTPException(401, "No logged in provider specified")


IN_APP_CONFIG = ActiveConfig()
if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    IN_APP_CONFIG.validate = True
IN_APP_CONFIG.auth_token = os.environ.get("FUNDIVERSE_API_SECRET_KEY")


def run_task(config: ActiveConfig, guid: str, func: Callable, *args, **kwargs):
    task = AsyncTask(
        guid=guid,
        status=BackgroundStatus.RUNNING,
        started=datetime.now(tz=UTC),
        result=None,
    )
    config.background_tasks[guid] = task

    try:
        task.result = func(*args, **kwargs)
        task.status = BackgroundStatus.SUCCESS
    except Exception as e:
        task.error = e
        task.status = BackgroundStatus.FAILED
    config.background_tasks[guid] = task


def canonicalize_key(key: str | None) -> str:
    return str(key).strip()


async def validate_auth_token(token: Annotated[str, Depends(oauth2_scheme)]):
    if not IN_APP_CONFIG.validate:
        return True
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    valid = canonicalize_key(token) == canonicalize_key(IN_APP_CONFIG.auth_token)
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return valid


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    # Clean up the ML models and release the resources
    print("Shutting down...!")


## app definitions
app = FastAPI(lifespan=lifespan, dependencies=[Depends(validate_auth_token)])

## associate config for testing
app.in_app_config = IN_APP_CONFIG  # type: ignore

allowed_origins = [
    "app://.",
]
allow_origin_regex = "(app://.)"

# dev settings
# if not IN_APP_CONFIG.validate:
allowed_origins += [
    "http://localhost:8080",
    "http://localhost:8081",
    "http://localhost:8090",
]
allow_origin_regex = "(app://.)|(http://localhost:[0-9]+)"

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Authorization"],
    allow_origin_regex=allow_origin_regex,
)


## BEGIN REQUESTS
class LoginRequest(BaseModel):
    key: str
    secret: str
    provider: ProviderType
    extra_factor: str | int | None = None
    device_id: str | None = None
    trading_pin: str | None = None
    force: bool = False
    wait_for_external_auth: bool = False


class RealPortfolioOutput(BaseModel):
    name: str
    holdings: List[RealPortfolioElement]
    cash: Money | None
    provider: ProviderType | None
    profit_or_loss: Money | None = None
    profit_or_loss_v2: ProfitModel | None


class CompositePortfolioOutput(BaseModel):
    name: str
    holdings: List[RealPortfolioElement]
    cash: Money
    components: Dict[str, RealPortfolioOutput]
    target_size: float = 250_000
    refreshed_at: int
    profit_or_loss: Money | None = None
    profit_or_loss_v2: ProfitModel | None
    refresh_time: Dict[str, timedelta] = Field(default_factory=dict)


class OrderStatus(Enum):
    REQUESTED = "requested"
    SUCCESS = "filled"
    FAILED = "failed"
    PLACED = "placed"
    # PENDING = "placed"


class OrderItem(BaseModel):
    ticker: str
    order_type: OrderType
    value: Money | None
    qty: int | float | None
    provider: ProviderType
    status: OrderStatus | None
    message: str | None


class PurchaseOrderOutput(BaseModel):
    to_buy: List[OrderItem]


class ListMutation(BaseModel):
    list: str
    scale: float


class StockMutation(BaseModel):
    ticker: str
    scale: float | None
    min_weight: Optional[float] = None

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class ProviderResponse(BaseModel):
    available: List[ProviderType]


class PortfolioRequest(BaseModel):
    provider: ProviderType


class TargetPortfolioRequest(BaseModel):
    index: str
    reweight: bool = False
    stock_exclusions: List[str] = Field(default_factory=list)
    list_exclusions: List[str] = Field(default_factory=list)
    stock_modifications: List[StockMutation] = Field(default_factory=list)
    list_modifications: List[ListMutation] = Field(default_factory=list)
    purchase_strategy: PurchaseStrategy = PurchaseStrategy.LARGEST_DIFF_FIRST
    provider: ProviderType | None = None
    providers: List[ProviderType] = Field(default_factory=list)


class BuyRequest(TargetPortfolioRequest):
    to_purchase: float
    target_size: float


class BuyRequestFinal(BaseModel):
    plan: OrderPlan
    provider: ProviderType | None = None


class BuyRequestFinalMultiProvider(BaseModel):
    plan: PurchaseOrderOutput
    providers: list[ProviderType]


class BuyRequestFinalMultiProviderOutput(BaseModel):
    orders: List[OrderItem]


class CompositePortfolioRefreshRequest(BaseModel):
    key: str
    providers: List[ProviderType]
    providers_to_refresh: List[ProviderType]


## Shared Functions


def get_provider_safe(iprovider: ProviderType | None = None) -> BaseProvider:
    _provider = iprovider or IN_APP_CONFIG.default_provider
    try:
        if _provider == ProviderType.ALPACA:
            provider = IN_APP_CONFIG.provider_cache.get(
                ProviderType.ALPACA, AlpacaProvider()
            )
            IN_APP_CONFIG.provider_cache[ProviderType.ALPACA] = provider
        elif _provider == ProviderType.ALPACA_PAPER:
            provider = IN_APP_CONFIG.provider_cache.get(
                ProviderType.ALPACA_PAPER, PaperAlpacaProvider()
            )
            IN_APP_CONFIG.provider_cache[ProviderType.ALPACA_PAPER] = provider
        elif _provider == ProviderType.ROBINHOOD:
            # Robinhood requires potential two factor auth
            # cannot safely instantiate default handler
            # even in dev

            rh_provider = IN_APP_CONFIG.provider_cache.get(ProviderType.ROBINHOOD, None)
            if rh_provider:
                IN_APP_CONFIG.provider_cache[ProviderType.ROBINHOOD] = rh_provider
                provider = rh_provider
            else:
                raise HTTPException(401, "No logged in robinhood provider found")

        elif _provider == ProviderType.WEBULL:
            wb_provider = IN_APP_CONFIG.provider_cache.get(ProviderType.WEBULL, None)
            if wb_provider:
                IN_APP_CONFIG.provider_cache[ProviderType.WEBULL] = wb_provider
                provider = wb_provider
            else:
                raise HTTPException(401, "No logged in webull provider found")

        elif _provider == ProviderType.WEBULL_PAPER:
            wb_paper_provider = IN_APP_CONFIG.provider_cache.get(
                ProviderType.WEBULL_PAPER, None
            )
            if wb_paper_provider:
                IN_APP_CONFIG.provider_cache[ProviderType.WEBULL_PAPER] = wb_paper_provider
                provider = wb_paper_provider
            else:
                raise HTTPException(401, "No logged in webull provider found")
        elif _provider == ProviderType.SCHWAB:
            schwab_provider = IN_APP_CONFIG.provider_cache.get(ProviderType.SCHWAB, None)
            if schwab_provider:
                IN_APP_CONFIG.provider_cache[ProviderType.SCHWAB] = schwab_provider
                provider = schwab_provider
            else:
                raise HTTPException(401, "No logged in schwab provider found")

        elif _provider is None:
            raise HTTPException(401, "No logged in provider specified")
        else:
            raise HTTPException(404, f"Provider type {_provider} not found")
    except ConfigurationError:
        raise HTTPException(401, "Provider is missing required auth information")
    return provider


## Begin Endpoints
router = APIRouter()


@router.get(
    "/",
)
async def healthcheck():
    return "healthy"


@router.get("/providers")
async def providers_handler():
    return ProviderResponse(available=AVAILABLE_PROVIDERS)


@router.get("/logged_in/{provider}")
async def logged_in_handler(provider):
    provider_enum = ProviderType(provider)
    return provider_enum in IN_APP_CONFIG.provider_cache


@router.post("/login")
def login_handler(input: LoginRequest):
    from os import environ

    # early exit if we have already logged in
    if not input.force and input.provider in IN_APP_CONFIG.provider_cache:
        return True
    try:
        if input.provider == ProviderType.ALPACA:
            environ[AlpacaProvider.API_KEY_VARIABLE] = input.key
            environ[AlpacaProvider.API_SECRET_VARIABLE] = input.secret
            # ensure we can login
            provider: BaseProvider = AlpacaProvider()
            IN_APP_CONFIG.provider_cache[input.provider] = provider
        elif input.provider == ProviderType.ALPACA_PAPER:
            environ[PaperAlpacaProvider.API_KEY_VARIABLE] = input.key
            environ[PaperAlpacaProvider.API_SECRET_VARIABLE] = input.secret
            # ensure we can login
            provider = PaperAlpacaProvider()
            IN_APP_CONFIG.provider_cache[input.provider] = provider
        elif input.provider == ProviderType.ROBINHOOD:
            environ["ROBINHOOD_USERNAME"] = input.key
            environ["ROBINHOOD_PASSWORD"] = input.secret
            # login using RH helper to handle
            # two factor auth
            rh_login(
                challenge_response=input.extra_factor,
                prior_response=IN_APP_CONFIG.pending_auth_response,
            )
            provider = RobinhoodProvider(external_auth=True)
            IN_APP_CONFIG.provider_cache[input.provider] = provider
            IN_APP_CONFIG.pending_auth_response = None
        elif input.provider == ProviderType.WEBULL:
            assert input.trading_pin is not None
            assert input.device_id is not None
            environ[WebullProvider.PASSWORD_ENV] = input.secret
            environ[WebullProvider.USERNAME_ENV] = input.key
            environ[WebullProvider.TRADE_TOKEN_ENV] = input.trading_pin
            environ[WebullProvider.DEVICE_ID_ENV] = input.device_id
            provider = WebullProvider()
            IN_APP_CONFIG.provider_cache[input.provider] = provider
        elif input.provider == ProviderType.WEBULL_PAPER:
            assert input.trading_pin is not None
            assert input.device_id is not None
            environ[WebullPaperProvider.PASSWORD_ENV] = input.secret
            environ[WebullPaperProvider.USERNAME_ENV] = input.key
            environ[WebullPaperProvider.TRADE_TOKEN_ENV] = input.trading_pin
            environ[WebullPaperProvider.DEVICE_ID_ENV] = input.device_id
            provider = WebullPaperProvider()
            IN_APP_CONFIG.provider_cache[input.provider] = provider
        elif input.provider == ProviderType.SCHWAB:
            environ[SchwabProvider.API_KEY_ENV] = input.key
            environ[SchwabProvider.APP_SECRET_ENV] = input.secret
            if IN_APP_CONFIG.pending_schwab_response and input.wait_for_external_auth:
                fetch_response(IN_APP_CONFIG.pending_schwab_response)
            lc = create_login_context(api_key=input.key, app_secret=input.secret)
            if lc:
                raise SchwabExtraAuthenticationStepException(response=lc)

            provider = SchwabProvider(external_auth=True)
            IN_APP_CONFIG.provider_cache[input.provider] = provider
            IN_APP_CONFIG.pending_schwab_response = None
        else:
            raise HTTPException(404, "Selected provider not supported yet")
        IN_APP_CONFIG.logged_in = input.provider.value

    except SchwabExtraAuthenticationStepException as e:
        IN_APP_CONFIG.pending_schwab_response = e.response
        raise HTTPException(303, e.response.authorization_url)
    except ExtraAuthenticationStepException as e:
        IN_APP_CONFIG.pending_auth_response = e.response
        raise HTTPException(412, f"Additional authentication required: {e}")
    except HTTPException as e:
        raise e
    except Exception as e:
        IN_APP_CONFIG.pending_auth_response = None
        raise HTTPException(400, f"Error logging in: {e}")


@router.get("/portfolio/")
async def get_portfolio_bare():
    provider = IN_APP_CONFIG.default_provider
    if not provider:
        raise HTTPException(401, "No logged in provider specified")
    return await get_portfolio(provider)


@router.get("/portfolio/{_provider}")
async def get_portfolio(_provider: ProviderType):
    provider = get_provider_safe(_provider)
    holdings = provider.get_holdings()
    IN_APP_CONFIG.holding_cache[_provider] = holdings
    return provider.get_holdings()


def refresh_sub_portfolio(
    key: ProviderType, providers_to_refresh: list[ProviderType]
) -> tuple[timedelta, RealPortfolio]:
    item: BaseProvider | None = IN_APP_CONFIG.provider_cache.get(key, None)
    start = datetime.now()
    if not item:
        raise HTTPException(
            401, f"Must log into {key} to refresh any element in this portfolio."
        )
    if key in providers_to_refresh:
        try:
            item.clear_cache(skip_clearing=["instrument_to_symbol_map"])
            rport = item.get_holdings()
            rport.profit_and_loss = item.get_profit_or_loss()
        except ConfigurationError:
            del IN_APP_CONFIG.provider_cache[key]
            raise
        except Exception as e:
            raise SubPortfolioRefreshException(error=e, provider=key)
        IN_APP_CONFIG.holding_cache[key] = rport
    else:
        rport = IN_APP_CONFIG.holding_cache[key]
    return datetime.now() - start, rport


@router.post("/composite_portfolio/refresh")
def refresh_composite_portfolio(input: CompositePortfolioRefreshRequest):
    active: Dict[str, RealPortfolioOutput] = {}
    raw = []
    profit_and_loss = ProfitModel(
        appreciation=Money(value=0.0), dividends=Money(value=0.0)
    )
    durations: Dict[str, timedelta] = {}
    with ThreadPoolExecutor(max_workers=10) as executor:
        portfolios = {
            executor.submit(refresh_sub_portfolio, key, input.providers_to_refresh)
            for key in input.providers
        }
        for future in as_completed(portfolios):
            try:
                duration, rport = future.result()
                if not rport.provider:
                    continue
                key = rport.provider.PROVIDER
                durations[key] = duration
                active[key] = RealPortfolioOutput(
                    name=f"{key.name}",
                    holdings=rport.holdings,
                    cash=rport.cash,
                    provider=key,
                    profit_or_loss_v2=rport.profit_and_loss,
                    profit_or_loss=(
                        rport.profit_and_loss.total if rport.profit_and_loss else None
                    ),
                )
                if rport.profit_and_loss:
                    profit_and_loss += rport.profit_and_loss
                raw.append(rport)
            except ConfigurationError:
                raise
            except HTTPException:
                raise
            except SubPortfolioRefreshException as e:
                raise HTTPException(
                    422, f"Error refreshing {e.provider}: {str(e.error)}"
                )
            except Exception as e:
                raise HTTPException(422, f"Error refreshing: {str(e)}")
    internal = CompositePortfolio(raw)
    return CompositePortfolioOutput(
        name=input.key,
        holdings=internal.holdings,
        cash=internal.cash,
        refresh_time=durations,
        components=active,
        refreshed_at=int(datetime.now(tz=UTC).timestamp()),
        profit_or_loss_v2=profit_and_loss,
        profit_or_loss=profit_and_loss.total,
    )


@router.get("/indexes")
async def list_indexes():
    _ = [INDEXES[x] for x in INDEXES.keys]
    return sorted(INDEXES.keys, reverse=True)


@router.get("/indexes_full")
async def list_indexes_full():
    # ensure we loaded
    _ = [INDEXES[x] for x in INDEXES.keys]
    return INDEXES


@router.get("/stock_lists")
async def stock_lists():
    # ensure we loaded
    _ = [STOCK_LISTS[x] for x in STOCK_LISTS.keys]
    return STOCK_LISTS


DEFAULT_MIN_WEIGHT = 0.001


def index_to_processed_index(
    input: TargetPortfolioRequest | BuyRequest,
) -> IdealPortfolio:
    try:
        ideal_port = deepcopy(INDEXES[input.index])
    except KeyError:
        raise HTTPException(404, f"Index {input.index} not found")

    if input.reweight:
        provider = get_provider_safe(input.provider)

        ideal_port.reweight_to_present(provider=provider)
    for mutation in input.stock_modifications:
        ideal_port.reweight(
            [mutation.ticker],
            weight=mutation.scale or 1.0,
            min_weight=mutation.min_weight or DEFAULT_MIN_WEIGHT,
        )
    for list_mutation in input.list_modifications:
        ideal_port.reweight(
            STOCK_LISTS[list_mutation.list],
            weight=list_mutation.scale,
            min_weight=DEFAULT_MIN_WEIGHT,
        )
    ideal_port.exclude(input.stock_exclusions)
    for item in input.list_exclusions:
        ideal_port.exclude(STOCK_LISTS[item])
    return ideal_port


@router.post("/generate_index")
def generate_index(input: TargetPortfolioRequest):
    if not input.index:
        raise HTTPException(400, "No index specified")
    return index_to_processed_index(input)


@router.get("/background_tasks/{guid}")
async def get_background_task(guid):
    response = IN_APP_CONFIG.background_tasks.get(guid)

    if not response:
        raise HTTPException(404, f"No background task found with guid {guid}")
    if response.status == BackgroundStatus.RUNNING:
        raise HTTPException(202, "Background task is still running")
    # for failure or success,
    # wipe the object to free memory
    elif response.status == BackgroundStatus.FAILED:
        del IN_APP_CONFIG.background_tasks[guid]
        # we will have stored the exception
        # raise it now
        raise response.error
        # raise HTTPException(500, f"Background task failed with error {response.error}")
    del IN_APP_CONFIG.background_tasks[guid]
    return response.result


def _plan_composite_purchase(input: BuyRequest):
    children = []
    buy_orders = {}
    for provider in input.providers:
        try:
            iprovider = get_provider_safe(provider)
            sub_port = sub_port = IN_APP_CONFIG.holding_cache.get(
                provider, iprovider.get_holdings()
            )
            buy_orders[provider] = input.purchase_strategy
            children.append(sub_port)
        except ConfigurationError as e:
            del IN_APP_CONFIG.provider_cache[provider]
            raise e
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                500, f"Error planning composite purchase: {e} on provider {provider}"
            )
    real_port = CompositePortfolio(children)
    ideal_port = index_to_processed_index(input)
    plan = generate_composite_order_plan(
        real_port,
        ideal_port,
        target_size=input.target_size,
        purchase_order_maps=buy_orders,
        target_order_size=Money(value=input.to_purchase or 0.0),
    )
    final = []
    for key, order_items in plan.items():
        for order in order_items.to_buy:
            final.append(
                OrderItem(
                    ticker=order.ticker,
                    order_type=order.order_type,
                    value=order.value,
                    qty=order.qty,
                    provider=key,
                    status=OrderStatus.REQUESTED,
                    message=None,
                )
            )
    output = PurchaseOrderOutput(to_buy=final)
    return output


@router.post("/plan_composite_purchase")
def plan_composite_purchase(input: BuyRequest):
    try:
        return _plan_composite_purchase(input)
    except ConfigurationError as e:
        raise e
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(500, f"Error planning composite purchase: {e}")


@router.get("/force_terminate")
async def force_terminate():
    raise ShutdownException("Terminating server")


@router.get("/terminate")
async def terminate():
    if not IN_APP_CONFIG.validate:
        return HTTPException(
            401,
            "Not in a pyinstaller bundle, running in dev mode "
            "and will not terminate by default."
            "curl get to /force_terminate to terminate instead.",
        )
    raise ShutdownException("Terminating server")


@router.get("/stock_info/{ticker}")
async def stock_info(ticker: str):
    provider = get_provider_safe()
    if not provider:
        return HTTPException(401, "No logged in provider specified")
    return provider.get_stock_info(ticker)


@router.post("/buy_index_from_plan")
def buy_index_from_plan(input: BuyRequestFinal):
    provider = get_provider_safe(input.provider)
    try:
        provider.purchase_order_plan(plan=input.plan)
    except OrderError as e:
        raise HTTPException(500, e.message)


def place_orders(
    orders: List[OrderItem], provider: BaseProvider, stale_providers: set[ProviderType]
):
    output = []
    for order in orders:
        if order.provider in stale_providers:
            order.status = OrderStatus.FAILED
            order.message = "Provider had a login error on an earlier order"
            output.append(order)
            continue
        try:
            transformed_order = OrderElement(
                ticker=order.ticker,
                order_type=order.order_type,
                value=order.value,
                qty=order.qty,
            )
            logger.info(f"Placing order for {order.ticker} with {order.provider}")
            provider.handle_order_element(transformed_order)
            order.status = OrderStatus.PLACED
            output.append(order)
        except OrderError as e:
            order.status = OrderStatus.FAILED
            order.message = e.message
            output.append(order)
        except ConfigurationError as e:
            stale_providers.add(order.provider)
            order.status = OrderStatus.FAILED
            order.message = str(e)
            output.append(order)
        except Exception as e:
            order.status = OrderStatus.FAILED
            order.message = str(e)
            output.append(order)
    return output


@router.post("/buy_index_from_plan_multi_provider")
def buy_index_from_plan_multi_provider(input: BuyRequestFinalMultiProvider):
    providers: Dict[ProviderType, BaseProvider] = {
        p: IN_APP_CONFIG.provider_cache.get(p) for p in input.providers  # type: ignore
    }
    if not all(providers.values()):
        raise HTTPException(401, "Not all providers are logged in")
    # check each of our p
    output: List[OrderItem] = []
    stale_providers: set[ProviderType] = set()
    grouped = defaultdict(list)
    for order in input.plan.to_buy:
        grouped[order.provider].append(order)

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(place_orders, orders, providers[key], stale_providers)
            for key, orders in grouped.items()
        }
        for future in as_completed(futures):
            output += future.result()
    for provider in stale_providers:
        if provider in IN_APP_CONFIG.provider_cache:
            del IN_APP_CONFIG.provider_cache[provider]
    return BuyRequestFinalMultiProviderOutput(orders=output)


class SleepRequest(BaseModel):
    sleep: int


@router.post("/long_sleep")
def long_sleep(sleep: SleepRequest):
    import time

    time.sleep(sleep.sleep)
    return {"slept": sleep.sleep}


def _get_last_exc():
    exc_type, exc_value, exc_traceback = sys.exc_info()
    sTB = "\n".join(traceback.format_tb(exc_traceback))
    return f"{exc_type}\n - msg: {exc_value}\n stack: {sTB}"


async def exit_app():
    for task in asyncio.all_tasks():
        print(f"cancelling task: {task}")
        try:
            task.cancel()
        except Exception:
            print(f"Task kill failed: {_get_last_exc()}")
            pass
    asyncio.gather(*asyncio.all_tasks())
    loop = asyncio.get_running_loop()
    loop.stop()
    raise ShutdownException("Server is shutting down")


## Build async routes
router_routes = list(router.routes)
for path in router_routes:
    if not isinstance(path, APIRoute):
        continue
    if "POST" in path.methods:

        def make_function(endpoint):
            args = get_type_hints(endpoint)

            async def dynamic_route_handler(
                background_tasks: BackgroundTasks,
                arg: Any = Body(None),
            ):
                guid = str(uuid.uuid4())
                arg_model: BaseModel = list(args.values())[0]
                parsed_arg = arg_model.model_validate(arg)
                background_tasks.add_task(
                    run_task, IN_APP_CONFIG, guid, endpoint, parsed_arg
                )
                return {"guid": guid}

            return dynamic_route_handler

        local_func = make_function(path.endpoint)
        new_path = f"/async_{path.path[1:]}"
        router.post(new_path)(local_func)


@app.exception_handler(ShutdownException)
async def shutdown_handler(request: Request, exc: ConfigurationError):
    task = BackgroundTask(exit_app)
    return PlainTextResponse(
        "Server is shutting down", status_code=503, background=task
    )


@app.exception_handler(ConfigurationError)
async def provider_auth_handler(request: Request, exc: ConfigurationError):
    return JSONResponse(
        status_code=401,
        content=jsonable_encoder({"detail": str(exc)}),
    )


app.include_router(router)


# @router.post("/async_plan_composite_purchase")
# def async_plan_composite_purchase(input: BuyRequest, background_tasks: BackgroundTasks):


def run():
    LOGGING_CONFIG["disable_existing_loggers"] = True
    import sys

    if os.environ.get("in-ci"):
        print("Running in a unit test, exiting")
        sys.exit(0)
    elif getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        print("running in a PyInstaller bundle, sending stdout to devnull")
        f = open(os.devnull, "w")
        sys.stdout = f
        run = uvicorn.run(
            app,
            host="0.0.0.0",
            port=SERVE_PORT,
            log_level="info",
            log_config=LOGGING_CONFIG,
        )
    else:
        print("Running in a normal Python process, assuming dev")

        def run():
            return uvicorn.run(
                "main:app",
                host="0.0.0.0",
                port=SERVE_PORT,
                log_level="info",
                log_config=LOGGING_CONFIG,
                reload=True,
            )

    try:
        run()
    except ShutdownException:
        print("Server is shutting down due to excepted shutdown call")
        sys.exit(0)
    except Exception as e:
        print(f"Server is shutting down due to {e}")
        sys.exit(1)


if __name__ == "__main__":
    multiprocessing.freeze_support()
    run()
