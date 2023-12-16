from typing import List, Dict, Annotated, Callable, Any
import dotenv

dotenv.load_dotenv()
import os
import sys
import multiprocessing
import uvicorn
import uuid
from enum import Enum
from datetime import datetime
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
from fastapi.routing import APIRoute
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dataclasses import dataclass, field
from py_portfolio_index.exceptions import OrderError, ExtraAuthenticationStepException
from py_portfolio_index.portfolio_providers.base_portfolio import BaseProvider
from py_portfolio_index.portfolio_providers.helpers.robinhood import login as rh_login
from fastapi.encoders import jsonable_encoder
from py_portfolio_index.models import (
    CompositePortfolio,
    RealPortfolio,
    LoginResponse,
    RealPortfolioElement,
    Money,
    OrderType,
    OrderElement,
)
from pytz import UTC

from typing import get_type_hints

from py_portfolio_index import (
    INDEXES,
    STOCK_LISTS,
    AlpacaProvider,
    PaperAlpacaProvider,
    RobinhoodProvider,
    WebullProvider,
    WebullPaperProvider,
    PurchaseStrategy,
    generate_composite_order_plan,
    AVAILABLE_PROVIDERS,
    Logger
)
from py_portfolio_index.models import OrderPlan
from py_portfolio_index.exceptions import ConfigurationError
from py_portfolio_index.enums import Provider
from pydantic import BaseModel, Field

from copy import deepcopy

# from py_portfolio_index.models import RealPortfolio
from fastapi.responses import PlainTextResponse
from starlette.background import BackgroundTask
import asyncio
import traceback
from logging import getLogger, StreamHandler

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

SERVE_PORT = 3042

logger = getLogger(__name__)
# hook into py-portfolio-index-logger
Logger.addHandler(StreamHandler())
logger.addHandler(StreamHandler())


class ShutdownException(Exception):
    pass


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
    provider_cache: Dict[Provider, BaseProvider] = field(default_factory=dict)
    holding_cache: Dict[Provider, RealPortfolio] = field(default_factory=dict)
    pending_auth_response: LoginResponse | None = None
    auth_token: str | None = None
    validate: bool = False
    background_tasks: Dict[str, AsyncTask] = field(default_factory=dict)

    @property
    def default_provider(self):
        # get the fastest provider
        priority = [Provider.ALPACA, Provider.ALPACA_PAPER, Provider.ROBINHOOD,
                    Provider.WEBULL, Provider.WEBULL_PAPER]
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


## app definitions
app = FastAPI(dependencies=[Depends(validate_auth_token)])

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
    provider: Provider
    extra_factor: str | int | None = None
    device_id: str | None = None
    trading_pin: str | None = None
    force: bool = False


class RealPortfolioOutput(BaseModel):
    name: str
    holdings: List[RealPortfolioElement]
    cash: Money | None
    provider: Provider | None
    profit_or_loss: Money | None = None


class CompositePortfolioOutput(BaseModel):
    name: str
    holdings: List[RealPortfolioElement]
    cash: Money
    components: Dict[str, RealPortfolioOutput]
    target_size: float = 250_000
    refreshed_at: int
    profit_and_loss: Money | None = None


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
    qty: int | None
    provider: Provider
    status: OrderStatus | None
    message: str | None


class PurchaseOrderOutput(BaseModel):
    to_buy: List[OrderItem]


class ListMutation(BaseModel):
    list: str
    scale: float


class StockMutation(BaseModel):
    ticker: str
    scale: float


class ProviderResponse(BaseModel):
    available: List[Provider]


class PortfolioRequest(BaseModel):
    provider: Provider


class TargetPortfolioRequest(BaseModel):
    index: str
    reweight: bool = False
    stock_exclusions: List[str] = Field(default_factory=list)
    list_exclusions: List[str] = Field(default_factory=list)
    stock_modifications: List[StockMutation] = Field(default_factory=list)
    list_modifications: List[ListMutation] = Field(default_factory=list)
    purchase_strategy: PurchaseStrategy = PurchaseStrategy.LARGEST_DIFF_FIRST
    provider: Provider | None = None
    providers: List[Provider] = Field(default_factory=list)


class BuyRequest(TargetPortfolioRequest):
    to_purchase: float
    target_size: float


class BuyRequestFinal(BaseModel):
    plan: OrderPlan
    provider: Provider | None = None


class BuyRequestFinalMultiProvider(BaseModel):
    plan: PurchaseOrderOutput
    providers: list[Provider]


class BuyRequestFinalMultiProviderOutput(BaseModel):
    orders: List[OrderItem]


class CompositePortfolioRefreshRequest(BaseModel):
    key: str
    providers: List[Provider]
    providers_to_refresh: List[Provider]


## Shared Functions


def get_provider_safe(iprovider: Provider | None = None) -> BaseProvider:
    _provider = iprovider or IN_APP_CONFIG.default_provider
    try:
        if _provider == Provider.ALPACA:
            provider = IN_APP_CONFIG.provider_cache.get(
                Provider.ALPACA, AlpacaProvider()
            )
            IN_APP_CONFIG.provider_cache[Provider.ALPACA] = provider
        elif _provider == Provider.ALPACA_PAPER:
            provider = IN_APP_CONFIG.provider_cache.get(
                Provider.ALPACA_PAPER, PaperAlpacaProvider()
            )
            IN_APP_CONFIG.provider_cache[Provider.ALPACA_PAPER] = provider
        elif _provider == Provider.ROBINHOOD:
            # Robinhood requires potential two factor auth
            # cannot safely instantiate default handler
            # even in dev
            rh_provider = IN_APP_CONFIG.provider_cache.get(Provider.ROBINHOOD, None)
            if not rh_provider:
                raise HTTPException(401, "No logged in robinhood provider found")
            IN_APP_CONFIG.provider_cache[Provider.ROBINHOOD] = rh_provider
            provider = rh_provider
        elif _provider == Provider.WEBULL:
            wb_provider = IN_APP_CONFIG.provider_cache.get(Provider.WEBULL, None)
            if not wb_provider:
                raise HTTPException(401, "No logged in webull provider found")
            IN_APP_CONFIG.provider_cache[Provider.WEBULL] = wb_provider
            provider = wb_provider
        elif _provider == Provider.WEBULL_PAPER:
            wb_paper_provider = IN_APP_CONFIG.provider_cache.get(Provider.WEBULL_PAPER, None)
            if not wb_provider:
                raise HTTPException(401, "No logged in webull provider found")
            IN_APP_CONFIG.provider_cache[Provider.WEBULL_PAPER] = wb_paper_provider
            provider = wb_paper_provider
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
    provider_enum = Provider(provider)
    return provider_enum in IN_APP_CONFIG.provider_cache


@router.post("/login")
def login_handler(input: LoginRequest):
    from os import environ

    # early exit if we have already logged in
    if not input.force and input.provider in IN_APP_CONFIG.provider_cache:
        return True
    try:
        if input.provider == Provider.ALPACA:
            environ[AlpacaProvider.API_KEY_VARIABLE] = input.key
            environ[AlpacaProvider.API_SECRET_VARIABLE] = input.secret
            # ensure we can login
            provider: BaseProvider = AlpacaProvider()
            IN_APP_CONFIG.provider_cache[input.provider] = provider
        elif input.provider == Provider.ALPACA_PAPER:
            environ[PaperAlpacaProvider.API_KEY_VARIABLE] = input.key
            environ[PaperAlpacaProvider.API_SECRET_VARIABLE] = input.secret
            # ensure we can login
            provider = PaperAlpacaProvider()
            IN_APP_CONFIG.provider_cache[input.provider] = provider
        elif input.provider == Provider.ROBINHOOD:
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
        elif input.provider == Provider.WEBULL:
            environ[WebullProvider.PASSWORD_ENV] = input.secret
            environ[WebullProvider.USERNAME_ENV] = input.key
            environ[WebullProvider.TRADE_TOKEN_ENV] = input.trading_pin
            environ[WebullProvider.DEVICE_ID_ENV] = input.device_id
            provider = WebullProvider()
            IN_APP_CONFIG.provider_cache[input.provider] = provider
        elif input.provider == Provider.WEBULL_PAPER:
            environ[WebullPaperProvider.PASSWORD_ENV] = input.secret
            environ[WebullPaperProvider.USERNAME_ENV] = input.key
            environ[WebullPaperProvider.TRADE_TOKEN_ENV] = input.trading_pin
            environ[WebullPaperProvider.DEVICE_ID_ENV] = input.device_id
            provider = WebullPaperProvider()
            IN_APP_CONFIG.provider_cache[input.provider] = provider
        else:
            raise HTTPException(404, "Selected provider not supported yet")
        IN_APP_CONFIG.logged_in = input.provider.value
        IN_APP_CONFIG.pending_auth_response = None
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
async def get_portfolio(_provider: Provider):
    provider = get_provider_safe(_provider)
    holdings = provider.get_holdings()
    IN_APP_CONFIG.holding_cache[_provider] = holdings
    return provider.get_holdings()


@router.post("/composite_portfolio/refresh")
def refresh_composite_portfolio(input: CompositePortfolioRefreshRequest):
    active: Dict[str, RealPortfolioOutput] = {}
    raw = []
    profit_and_loss = Money(value=0.0)
    for key in input.providers:
        item = IN_APP_CONFIG.provider_cache.get(key, None)
        if not item:
            raise HTTPException(401, f"Must log into {key} to refresh any element in this portfolio.")
        # key, item in IN_APP_CONFIG.provider_cache.items():
        if key in input.providers_to_refresh:
            item.clear_cache()
            rport = item.get_holdings()
            rport.profit_and_loss = item.get_profit_or_loss()
            IN_APP_CONFIG.holding_cache[key] = rport
        else:
            rport = IN_APP_CONFIG.holding_cache[key]
        active[key] = RealPortfolioOutput(
            name=f"{key.name}",
            holdings=rport.holdings,
            cash=rport.cash,
            provider=key,
            profit_or_loss=rport.profit_and_loss,
        )
        profit_and_loss += rport.profit_and_loss
        raw.append(rport)
    internal = CompositePortfolio(raw)
    return CompositePortfolioOutput(
        name=input.key,
        holdings=internal.holdings,
        cash=internal.cash,
        components=active,
        refreshed_at=int(datetime.now(tz=UTC).timestamp()),
        profit_and_loss=profit_and_loss,
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


def index_to_processed_index(input: TargetPortfolioRequest | BuyRequest):
    try:
        ideal_port = deepcopy(INDEXES[input.index])
    except KeyError:
        raise HTTPException(404, f"Index {input.index} not found")


    if input.reweight:
        provider = get_provider_safe(input.provider)

        ideal_port.reweight_to_present(provider=provider)
    for mutation in input.stock_modifications:
        ideal_port.reweight([mutation.ticker], weight=mutation.scale, min_weight=0.001)
    for list_mutation in input.list_modifications:
        ideal_port.reweight(
            STOCK_LISTS[list_mutation.list],
            weight=list_mutation.scale,
            min_weight=0.001,
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


@router.post("/plan_composite_purchase")
def plan_composite_purchase(input: BuyRequest):
    children = []
    buy_orders = {}
    for provider in input.providers:
        iprovider = get_provider_safe(provider)
        sub_port = iprovider.get_holdings()
        buy_orders[provider] = input.purchase_strategy
        children.append(sub_port)
    real_port = CompositePortfolio(children)
    ideal_port = index_to_processed_index(input)
    plan = generate_composite_order_plan(
        real_port,
        ideal_port,
        purchase_power=input.to_purchase,
        target_size=input.target_size,
        purchase_order_maps=buy_orders,
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


@router.post("/buy_index_from_plan_multi_provider")
def buy_index_from_plan_multi_provider(input: BuyRequestFinalMultiProvider):
    providers: Dict[Provider, BaseProvider] = {
        p: IN_APP_CONFIG.provider_cache.get(p) for p in input.providers  # type: ignore
    }
    if not all(providers.values()):
        raise HTTPException(403, "Not all providers are logged in")
    # check each of our p
    output: List[OrderItem] = []
    for order in input.plan.to_buy:
        try:
            transformed_order = OrderElement(
                ticker=order.ticker,
                order_type=order.order_type,
                value=order.value,
                qty=order.qty,
            )
            logger.info(f'Placing order for {order.ticker} with {order.provider}')
            providers[order.provider].handle_order_element(transformed_order)
            order.status = OrderStatus.PLACED
            output.append(order)
        except OrderError as e:
            order.status = OrderStatus.FAILED
            order.message = e.message
            output.append(order)
        except Exception as e:
            order.status = OrderStatus.FAILED
            order.message = str(e)
            output.append(order)
    return BuyRequestFinalMultiProviderOutput(orders=output)


class SleepRequest(BaseModel):
    sleep: int


@router.post("/long_sleep")
def long_sleep(sleep: SleepRequest):
    import time

    time.sleep(sleep.sleep)
    return {"slept": sleep.sleep}


@app.on_event("shutdown")
def shutdown_event():
    print("Shutting down...!")


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
    raise ValueError("Server is shutting down")


# @app.exception_handler(HTTPException)
# async def http_exception_handler(request, exc: HTTPException):
#     """Override the default exception handler to allow for graceful shutdowns"""
#     if exc.status_code == 503:
#         # here is where we terminate all running processes

#     return JSONResponse(
#         status_code=exc.status_code,
#         content=jsonable_encoder(
#             {"detail": "Issue with provider authentication, you must re-login"}
#         ),
#     )


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
                arg_model:BaseModel = list(args.values())[0]
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

    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
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
    except Exception as e:
        print(f"Server is shutting down due to {e}")
        exit(0)


if __name__ == "__main__":
    multiprocessing.freeze_support()
    try:
        run()
        sys.exit(0)
    except:  # noqa: E722
        sys.exit(0)
