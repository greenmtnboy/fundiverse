from typing import List, Dict
import os
import sys
import multiprocessing
import uvicorn
from datetime import datetime
from uvicorn.config import LOGGING_CONFIG
from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dataclasses import dataclass, field
from py_portfolio_index.exceptions import OrderError, ExtraAuthenticationStepException
from py_portfolio_index.portfolio_providers.base_portfolio import BaseProvider
from py_portfolio_index.portfolio_providers.helpers.robinhood import login as rh_login
from py_portfolio_index.models import (
    CompositePortfolio,
    RealPortfolio,
    LoginResponse,
    RealPortfolioElement,
    Money,
    OrderType
)
from pytz import UTC

from py_portfolio_index import (
    INDEXES,
    STOCK_LISTS,
    AlpacaProvider,
    RobinhoodProvider,
    PurchaseStrategy,
    generate_order_plan,
    generate_composite_order_plan,
    AVAILABLE_PROVIDERS,
)
from py_portfolio_index.models import OrderPlan
from py_portfolio_index.exceptions import ConfigurationError
from py_portfolio_index.enums import Provider
from pydantic import BaseModel, Field


from copy import deepcopy

# from py_portfolio_index.models import RealPortfolio
from fastapi.responses import PlainTextResponse, Response
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.background import BackgroundTask
import asyncio
import traceback

app = FastAPI()


@dataclass
class ActiveConfig:
    logged_in: str | None = None
    provider: Provider | None = None
    provider_cache: Dict[Provider, BaseProvider] = field(default_factory=dict)
    holding_cache: Dict[Provider, RealPortfolio] = field(default_factory=dict)
    pending_auth_response: LoginResponse | None = None


IN_APP_CONFIG = ActiveConfig()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://localhost:8081",
        "http://localhost:8090",
        "app://.",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


## BEGIN REQUESTS
class LoginRequest(BaseModel):
    key: str
    secret: str
    provider: Provider
    extra_factor: str | int | None = None
    force: bool = False

class RealPortfolioOutput(BaseModel):
    name: str
    holdings: List[RealPortfolioElement]
    cash: Money
    provider: Provider | None


class CompositePortfolioOutput(BaseModel):
    name: str
    holdings: List[RealPortfolioElement]
    cash: Money
    components: Dict[str, RealPortfolioOutput]
    target_size: float = 250_000
    refreshed_at: int

class OrderItem(BaseModel):
    ticker: str
    order_type: OrderType
    value: Money | None
    qty: int | None
    provider:Provider


class PurchaseOrderOutput(BaseModel):
    to_buy:List[OrderItem]

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
    stock_exclusions: None | List[str] = Field(default_factory=list)
    list_exclusions: None | List[str] = Field(default_factory=list)
    stock_modifications: None | List[StockMutation] = Field(default_factory=list)
    list_modifications: None | List[ListMutation] = Field(default_factory=list)
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


class CompositePortfolioRefreshRequest(BaseModel):
    key: str
    providers: List[Provider]
    providers_to_refresh: List[Provider]


## Shared Functions


def get_provider_safe(iprovider: Provider | None = None) -> BaseProvider:
    _provider = iprovider or IN_APP_CONFIG.provider
    try:
        if _provider == Provider.ALPACA:
            provider = IN_APP_CONFIG.provider_cache.get(
                Provider.ALPACA, AlpacaProvider()
            )
            IN_APP_CONFIG.provider_cache[Provider.ALPACA] = provider
        elif _provider == Provider.ROBINHOOD:
            # Robinhood requires potential two factor auth
            # cannot safely instantiate default handler
            # even in dev
            provider = IN_APP_CONFIG.provider_cache.get(Provider.ROBINHOOD, None)
            if not provider:
                raise HTTPException(401, "No logged in robinhood provider found")
            IN_APP_CONFIG.provider_cache[Provider.ROBINHOOD] = provider
        elif _provider is None:
            raise HTTPException(401, "No logged in provider specified")
        else:
            raise HTTPException(404, f"Provider type {_provider} not found")
    except ConfigurationError:
        raise HTTPException(401, "Provider is missing required auth information")
    return provider


## Begin Endpoints
router = APIRouter()


@router.get("/")
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
async def login_handler(input: LoginRequest):
    from os import environ

    # early exit if we have already logged in
    if not input.force and input.provider in IN_APP_CONFIG.provider_cache:
        return True
    try:
        if input.provider == Provider.ALPACA:
            environ["ALPACA_API_KEY"] = input.key
            environ["ALPACA_API_SECRET"] = input.secret
            # ensure we can login
            provider = AlpacaProvider()
            IN_APP_CONFIG.provider_cache[Provider.ALPACA] = provider

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
            IN_APP_CONFIG.provider_cache[Provider.ROBINHOOD] = provider
        else:
            raise HTTPException(404, "Selected provider not supported yet")
        IN_APP_CONFIG.logged_in = input.provider.value
        IN_APP_CONFIG.provider = input.provider
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
    provider = IN_APP_CONFIG.provider
    if not provider:
        raise HTTPException(401, "No logged in provider specified")
    return await get_portfolio(IN_APP_CONFIG.provider)


@router.get("/portfolio/{_provider}")
async def get_portfolio(_provider: Provider):
    provider = get_provider_safe(_provider)
    holdings = provider.get_holdings()
    IN_APP_CONFIG.holding_cache[_provider] = holdings
    return provider.get_holdings()




@router.post("/composite_portfolio/refresh")
async def refresh_composite_portfolio(input: CompositePortfolioRefreshRequest):
    active: Dict[Provider, RealPortfolio] = {}
    raw = []
    for key in input.providers:
        item = IN_APP_CONFIG.provider_cache.get(key, None)
        if not item:
            raise HTTPException(401, f"Must log into {key} to refresh this portfolio.")
        # key, item in IN_APP_CONFIG.provider_cache.items():
        rport = item.get_holdings()
        IN_APP_CONFIG.holding_cache[key] = rport
        active[key] = RealPortfolioOutput(
            name=f"{key.name}",
            holdings=rport.holdings,
            cash=rport.cash,
            provider=key,
        )
        raw.append(rport)
    internal = CompositePortfolio(raw)
    return CompositePortfolioOutput(
        name=input.key,
        holdings=internal.holdings,
        cash=internal.cash,
        components=active,
        refreshed_at=datetime.now(tz=UTC).timestamp(),
    )


@router.get("/indexes")
async def list_indexes():
    _ = [INDEXES[x] for x in INDEXES.keys]
    return sorted(INDEXES.keys, reverse=True)


@router.get("/stock_lists")
async def stock_lists():
    # ensure we loaded
    _ = [STOCK_LISTS[x] for x in STOCK_LISTS.keys]
    return STOCK_LISTS


def index_to_processed_index(input: TargetPortfolioRequest | BuyRequest):
    ideal_port = deepcopy(INDEXES[input.index])
    ideal_port.exclude(input.stock_exclusions)

    if input.reweight:
        provider = get_provider_safe(input.provider)

        ideal_port.reweight_to_present(provider=provider)
    for item in input.list_exclusions:
        ideal_port.exclude(STOCK_LISTS[item])
    for mutation in input.stock_modifications:
        ideal_port.reweight([mutation.ticker], weight=mutation.scale, min_weight=0.001)
    for mutation in input.list_modifications:
        ideal_port.reweight(
            STOCK_LISTS[mutation.list], weight=mutation.scale, min_weight=0.001
        )
    return ideal_port


@router.post("/generate_index")
async def generate_index(input: TargetPortfolioRequest):
    return index_to_processed_index(input)


@router.post("/plan_composite_purchase")
async def plan_composite_purchase(input: BuyRequest):
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
        # purchase_power=input.to_purchase,
        target_size=input.target_size,
        purchase_order_maps=buy_orders
    )
    final = []
    for key, order_items in plan.items():
        for order in order_items.to_buy:
            final.append(OrderItem(
                ticker=order.ticker,
                order_type=order.order_type,
                value=order.value,
                qty=order.qty,
                provider=key
            ))
    output = PurchaseOrderOutput(to_buy=final)
    return output


@router.post("/plan_purchase")
async def plan_purchase(input: BuyRequest):
    provider = get_provider_safe(input.provider)
    real_port = IN_APP_CONFIG.provider_cache.get(input.provider, None)
    if not real_port:
        print("have to rebuild real portfolio")
        print(input.provider)
        print(IN_APP_CONFIG.provider_cache.keys())
        real_port = provider.get_holdings()
    ideal_port = index_to_processed_index(input)
    plan = generate_order_plan(
        real_port,
        ideal_port,
        purchase_power=input.to_purchase,
        target_size=input.target_size,
        buy_order=input.purchase_strategy,
    )
    return plan


@router.get("/terminate")
async def terminate():
    raise HTTPException(503, "Terminating server")


@router.post("/buy_index_from_plan")
async def buy_index_from_plan(input: BuyRequestFinal):
    provider = get_provider_safe(input.provider)
    try:
        provider.purchase_order_plan(plan=input.plan)
    except OrderError as e:
        raise HTTPException(500, e.message)


@router.post("/buy_index_from_plan_multi_provider")
async def buy_index_from_plan_multi_provider(input: BuyRequestFinalMultiProvider):
    providers = {p:IN_APP_CONFIG.provider_cache[p] for p in input.providers}
    # check each of our p
    successful = []
    for order in input.plan.to_buy:
        providers[order.provider].handle_order_element(order)
    


app.include_router(router)


@app.on_event("shutdown")
def shutdown_event():
    print("Shutting down...!")


def _get_last_exc():
    exc_type, exc_value, exc_traceback = sys.exc_info()
    sTB = "\n".join(traceback.format_tb(exc_traceback))
    return f"{exc_type}\n - msg: {exc_value}\n stack: {sTB}"


async def exit_app():
    if asyncio.Task:
        for task in asyncio.all_tasks():
            print(f"cancelling task: {task}")
            try:
                task.cancel()
            except Exception:
                print(f"Task kill failed: {_get_last_exc()}")
                pass
    asyncio.gather(asyncio.all_tasks())
    loop = asyncio.get_running_loop()
    loop.stop()


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    if exc.status_code == 503:
        task = BackgroundTask(exit_app)
        return PlainTextResponse(
            "Server is shutting down", status_code=exc.status_code, background=task
        )
    return Response(
        status_code=exc.status_code, headers=exc.headers, content=exc.detail
    )


def run():
    LOGGING_CONFIG["disable_existing_loggers"] = True
    import sys

    dev = True
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        print("running in a PyInstaller bundle, setting sys.stdout to devnull")

        f = open(os.devnull, "w")
        sys.stdout = f
        dev = False
    else:
        print("Running in a normal Python process, assuming dev")
    try:
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=3000,
            log_level="info",
            log_config=LOGGING_CONFIG,
            reload=dev,
        )
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
