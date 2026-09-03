import os
import sys
from collections.abc import Callable
from typing import Annotated, Any

import dotenv

dotenv.load_dotenv()
import asyncio
import multiprocessing
import uuid
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import asynccontextmanager
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from logging import StreamHandler, getLogger
from os import environ
from pathlib import Path
from typing import get_type_hints

import uvicorn
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Body,
    Depends,
    FastAPI,
    HTTPException,
    Request,
    status,
)
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.routing import APIRoute
from fastapi.security import OAuth2PasswordBearer
from py_portfolio_index import (
    AVAILABLE_PROVIDERS,
    INDEXES,
    STOCK_LISTS,
    AlpacaProvider,
    ETradeProvider,
    Logger,
    MooMooProvider,
    PaperAlpacaProvider,
    PurchaseStrategy,
    RobinhoodProvider,
    SchwabProvider,
    WebullProvider,
    generate_composite_order_plan,
)
from py_portfolio_index.datastores.duckdb_datastore import DuckDBDatastore
from py_portfolio_index.enums import Currency, ProviderType
from py_portfolio_index.exceptions import (
    ConfigurationError,
    ExtraAuthenticationStepException,
    OrderError,
)
from py_portfolio_index.models import (
    CompositePortfolio,
    IdealPortfolio,
    Money,
    OrderElement,
    OrderPlan,
    OrderType,
    ProfitModel,
    RealPortfolio,
    RealPortfolioElement,
)
from py_portfolio_index.portfolio_providers.base_portfolio import BaseProvider
from py_portfolio_index.portfolio_providers.helpers.etrade import (
    ETradeAuthContext,
)
from py_portfolio_index.portfolio_providers.helpers.etrade import (
    complete_authorization as etrade_complete_authorization,
)
from py_portfolio_index.portfolio_providers.helpers.etrade import (
    create_login_context as etrade_create_login_context,
)
from py_portfolio_index.portfolio_providers.helpers.etrade import (
    load_cached_token as etrade_load_cached_token,
)
from py_portfolio_index.portfolio_providers.helpers.robinhood import (
    login as rh_login,
)
from py_portfolio_index.portfolio_providers.helpers.schwab import (
    SchwabAuthContext,
    create_login_context,
    fetch_response,
)
from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel
from pytz import UTC
from starlette.background import BackgroundTask
from uvicorn.config import LOGGING_CONFIG

from config import ActiveConfig, BackgroundStatus, run_task
from exports import (
    DatabaseExportRequest,
    export_portfolio_to_database,
)

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


class ETradeExtraAuthenticationStepException(Exception):
    def __init__(self, response: ETradeAuthContext, *args):
        super().__init__(*args)
        self.response = response


def schwab_context_is_live(context: SchwabAuthContext) -> bool:
    """Whether a pending schwab auth context can still complete.

    A context is only usable while the subprocess holding the callback port is
    alive; that process is what puts the redirect on the queue fetch_response
    waits on. Once it is gone the context can never be redeemed.
    """
    import psutil

    pid = context.server_pid
    if pid is None:
        return False
    try:
        return psutil.Process(pid).is_running()
    except psutil.Error:
        return False


def discard_schwab_context(context: SchwabAuthContext) -> None:
    """Release a context we are giving up on, freeing the callback port.

    A leaked server keeps listening on the callback port, so it would intercept
    the redirect meant for whatever context comes next.
    """
    import psutil

    IN_APP_CONFIG.pending_schwab_response = None
    if context.server_pid is None:
        return
    try:
        psutil.Process(context.server_pid).kill()
    except psutil.Error:
        pass


# Add to the request models section


# Add helper function to get database path
def get_database_path(portfolio_name: str) -> Path:
    """Get canonical storage location for portfolio database"""
    db_dir = Path.home() / ".fundiverse" / "databases"
    db_dir.mkdir(parents=True, exist_ok=True)
    return db_dir / f"{portfolio_name}.db"


IN_APP_CONFIG = ActiveConfig()
if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    IN_APP_CONFIG.validate = True
IN_APP_CONFIG.auth_token = os.environ.get("FUNDIVERSE_API_SECRET_KEY")


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
    allow_headers=["Authorization", "Cache-Control", "Pragma", "Expires"],
    allow_origin_regex=allow_origin_regex,
)


## BEGIN REQUESTS
class LoginRequest(BaseModel):
    key: str
    secret: str
    provider: ProviderType
    extra_factor: str | int | None = None
    trading_pin: str | None = None
    proxy_path: str | None = None
    force: bool = False
    wait_for_external_auth: bool = False
    quote_provider: ProviderType | None = None
    # etrade: target the sandbox environment; arrives as free text from the
    # login form, so anything truthy-looking counts
    sandbox: str | bool | None = None

    @property
    def sandbox_enabled(self) -> bool:
        if isinstance(self.sandbox, bool):
            return self.sandbox
        return str(self.sandbox or "").strip().lower() in ("1", "true", "yes", "on")


class ProviderStatus(str, Enum):
    """Per-provider outcome of a portfolio operation.

    Operations are partial by default: a provider that cannot be reached
    downgrades to its last known snapshot rather than failing the whole call.
    """

    # live data was fetched from the provider on this call
    REFRESHED = "refreshed"
    # provider was authenticated but deliberately not refreshed this call
    CACHED = "cached"
    # no login for this provider; any holdings shown are a stale snapshot
    UNAUTHENTICATED = "unauthenticated"
    # login exists but the refresh itself failed
    ERROR = "error"


#: statuses where the data shown is not live
STALE_STATUSES = {
    ProviderStatus.CACHED,
    ProviderStatus.UNAUTHENTICATED,
    ProviderStatus.ERROR,
}
#: statuses that mean the provider cannot participate in orders
UNUSABLE_STATUSES = {ProviderStatus.UNAUTHENTICATED, ProviderStatus.ERROR}

_CURRENCY_ALIASES = {"USD": "$", "EUR": "€", "GBP": "£"}
_CURRENCY_VALUES = {c.value for c in Currency}


def _coerce_currency(value: Any) -> Any:
    """Rewrite currency codes into the symbols py-portfolio-index expects.

    Client snapshots are replayed out of long-lived local storage, which has
    accumulated both ``USD`` and ``$`` spellings over time.
    """
    if isinstance(value, dict):
        out = dict(value)
        currency = out.get("currency")
        if isinstance(currency, str) and currency not in _CURRENCY_VALUES:
            resolved = _CURRENCY_ALIASES.get(currency.upper())
            if resolved:
                out["currency"] = resolved
            else:
                out.pop("currency")
        return {k: _coerce_currency(v) for k, v in out.items()}
    if isinstance(value, list):
        return [_coerce_currency(v) for v in value]
    return value


class SnapshotHolding(BaseModel):
    """A holding replayed from a client-held cache.

    Deliberately more forgiving than RealPortfolioElement: this data may have
    been written by an older version of the app.
    """

    ticker: str
    units: Decimal = Decimal(0)
    value: Money = Field(default_factory=lambda: Money(value=0))
    weight: Decimal = Decimal(0)
    unsettled: bool = False
    dividends: Money = Field(default_factory=lambda: Money(value=0))
    appreciation: Money = Field(default_factory=lambda: Money(value=0))

    @model_validator(mode="before")
    @classmethod
    def _normalize(cls, values):
        return _coerce_currency(values)

    def to_element(self) -> RealPortfolioElement:
        return RealPortfolioElement(
            ticker=self.ticker,
            units=self.units,
            value=self.value,
            weight=self.weight,
            unsettled=self.unsettled,
            dividends=self.dividends,
            appreciation=self.appreciation,
        )


class ProviderSnapshot(BaseModel):
    """The client's last known state for one provider.

    Sent alongside partial operations so a provider the user has not logged
    into this session still contributes its holdings to composite totals and
    to purchase planning.
    """

    provider: ProviderType
    holdings: list[SnapshotHolding] = Field(default_factory=list)
    cash: Money = Field(default_factory=lambda: Money(value=0))
    profit_or_loss_v2: ProfitModel | None = None
    refreshed_at: int | None = None

    @model_validator(mode="before")
    @classmethod
    def _normalize(cls, values):
        return _coerce_currency(values)

    def to_portfolio(self) -> RealPortfolio:
        # provider is left unset: an un-authenticated snapshot must never be
        # picked up as an order destination by generate_composite_order_plan
        return RealPortfolio(
            holdings=[h.to_element() for h in self.holdings],
            cash=self.cash,
            profit_and_loss=self.profit_or_loss_v2,
            provider=None,
        )


class RealPortfolioOutput(BaseModel):
    name: str
    holdings: list[RealPortfolioElement]
    cash: Money | None
    provider: ProviderType | None
    holding_size: Money | None = None
    profit_or_loss: Money | None = None
    profit_or_loss_v2: ProfitModel | None
    status: ProviderStatus = ProviderStatus.REFRESHED
    error: str | None = None
    refreshed_at: int | None = None


class CompositePortfolioOutput(BaseModel):
    name: str
    holdings: list[RealPortfolioElement]
    cash: Money
    components: dict[str, RealPortfolioOutput]
    target_size: float = 250_000
    refreshed_at: int
    profit_or_loss: Money | None = None
    profit_or_loss_v2: ProfitModel | None
    refresh_time: dict[str, timedelta] = Field(default_factory=dict)
    #: cash that can actually be spent right now, i.e. held at a provider we
    #: are authenticated to. `cash` includes un-authenticated providers.
    investable_cash: Money = Field(default_factory=lambda: Money(value=0))
    #: true when at least one provider is showing stale or missing data
    partial: bool = False
    #: providers that contributed no live data on this refresh
    degraded_providers: list[ProviderType] = Field(default_factory=list)


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
    to_buy: list[OrderItem]
    #: providers whose holdings were counted from a stale snapshot and which
    #: therefore received no orders
    skipped_providers: list[ProviderType] = Field(default_factory=list)
    #: providers that orders will actually be routed to
    order_providers: list[ProviderType] = Field(default_factory=list)


class ListMutation(BaseModel):
    list: str
    scale: float


class StockMutation(BaseModel):
    ticker: str
    scale: float | None
    min_weight: float | None = None

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class ProviderResponse(BaseModel):
    available: list[ProviderType]


class PortfolioRequest(BaseModel):
    provider: ProviderType


class TargetPortfolioRequest(BaseModel):
    index: str
    reweight: bool = False
    stock_exclusions: list[str] = Field(default_factory=list)
    list_exclusions: list[str] = Field(default_factory=list)
    stock_modifications: list[StockMutation] = Field(default_factory=list)
    list_modifications: list[ListMutation] = Field(default_factory=list)
    purchase_strategy: PurchaseStrategy = PurchaseStrategy.LARGEST_DIFF_FIRST
    provider: ProviderType | None = None
    providers: list[ProviderType] = Field(default_factory=list)


class PartialOperationRequest(BaseModel):
    """Mixin for operations that tolerate partially authenticated portfolios.

    ``require_all`` restores the old all-or-nothing behaviour for callers that
    genuinely need every provider present.
    """

    require_all: bool = False
    #: client-held snapshots for providers we may not be logged into
    cached: list[ProviderSnapshot] = Field(default_factory=list)


class BuyRequest(TargetPortfolioRequest, PartialOperationRequest):
    to_purchase: float
    target_size: float


class BuyRequestFinal(BaseModel):
    plan: OrderPlan
    provider: ProviderType | None = None


class BuyRequestFinalMultiProvider(BaseModel):
    plan: PurchaseOrderOutput
    providers: list[ProviderType]
    require_all: bool = False


class BuyRequestFinalMultiProviderOutput(BaseModel):
    orders: list[OrderItem]
    #: providers that were skipped because we are not authenticated to them
    skipped_providers: list[ProviderType] = Field(default_factory=list)


class CompositePortfolioRefreshRequest(PartialOperationRequest):
    key: str
    providers: list[ProviderType]
    #: providers to fetch live data for. Omit (or send null) to refresh every
    #: provider we are currently authenticated to - the partial default.
    providers_to_refresh: list[ProviderType] | None = None


class ProviderStatusOutput(BaseModel):
    provider: ProviderType
    authenticated: bool
    has_cached_holdings: bool
    refreshed_at: int | None = None


class ProviderStatusResponse(BaseModel):
    providers: list[ProviderStatusOutput]


## Shared Functions


def get_provider_safe(iprovider: ProviderType | None = None) -> BaseProvider:
    _provider = iprovider or IN_APP_CONFIG.default_provider
    try:
        if _provider == ProviderType.ALPACA:
            # constructed lazily: building a provider we already have cached
            # re-reads the environment and fails when credentials only ever
            # arrived through the login endpoint
            provider = IN_APP_CONFIG.provider_cache.get(ProviderType.ALPACA) or AlpacaProvider()
            IN_APP_CONFIG.provider_cache[ProviderType.ALPACA] = provider
        elif _provider == ProviderType.ALPACA_PAPER:
            provider = (
                IN_APP_CONFIG.provider_cache.get(ProviderType.ALPACA_PAPER)
                or PaperAlpacaProvider()
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

        elif _provider == ProviderType.SCHWAB:
            schwab_provider = IN_APP_CONFIG.provider_cache.get(
                ProviderType.SCHWAB, None
            )
            if schwab_provider:
                IN_APP_CONFIG.provider_cache[ProviderType.SCHWAB] = schwab_provider
                provider = schwab_provider
            else:
                raise HTTPException(401, "No logged in schwab provider found")
        elif _provider == ProviderType.ETRADE:
            etrade_provider = IN_APP_CONFIG.provider_cache.get(ProviderType.ETRADE, None)
            if etrade_provider:
                IN_APP_CONFIG.provider_cache[ProviderType.ETRADE] = etrade_provider
                provider = etrade_provider
            else:
                raise HTTPException(401, "No logged in etrade provider found")
        elif _provider == ProviderType.MOOMOO:
            momoo_provider = IN_APP_CONFIG.provider_cache.get(ProviderType.MOOMOO, None)
            if momoo_provider:
                IN_APP_CONFIG.provider_cache[ProviderType.MOOMOO] = momoo_provider
                provider = momoo_provider
            else:
                raise HTTPException(401, "No logged in moomoo provider found")
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


@router.get("/provider_status")
async def provider_status_handler():
    """Auth and cache state for every provider, in one call.

    Lets the client decide what a partial refresh should target without
    probing each provider individually.
    """
    out = []
    for provider in AVAILABLE_PROVIDERS:
        refreshed = IN_APP_CONFIG.holding_refreshed_at.get(provider)
        out.append(
            ProviderStatusOutput(
                provider=provider,
                authenticated=IN_APP_CONFIG.is_authenticated(provider),
                has_cached_holdings=provider in IN_APP_CONFIG.holding_cache,
                refreshed_at=int(refreshed.timestamp()) if refreshed else None,
            )
        )
    return ProviderStatusResponse(providers=out)


def _login_alpaca(input: LoginRequest) -> BaseProvider:
    environ[AlpacaProvider.API_KEY_VARIABLE] = input.key
    environ[AlpacaProvider.API_SECRET_VARIABLE] = input.secret
    # constructing the provider is what proves the credentials work
    return AlpacaProvider()


def _login_alpaca_paper(input: LoginRequest) -> BaseProvider:
    environ[PaperAlpacaProvider.API_KEY_VARIABLE] = input.key
    environ[PaperAlpacaProvider.API_SECRET_VARIABLE] = input.secret
    # constructing the provider is what proves the credentials work
    return PaperAlpacaProvider()


def _login_robinhood(input: LoginRequest) -> BaseProvider:
    environ["ROBINHOOD_USERNAME"] = input.key
    environ["ROBINHOOD_PASSWORD"] = input.secret
    # login using RH helper to handle
    # two factor auth
    rh_login(
        challenge_response=input.extra_factor,
        prior_response=IN_APP_CONFIG.pending_auth_response,
    )
    provider = RobinhoodProvider(external_auth=True)
    IN_APP_CONFIG.pending_auth_response = None
    return provider


def _login_webull(input: LoginRequest) -> BaseProvider:
    # the official OpenAPI SDK authenticates with an app key/secret pair
    # generated in the Webull developer portal
    environ[WebullProvider.API_KEY_ENV] = input.key
    environ[WebullProvider.API_SECRET_ENV] = input.secret
    return WebullProvider()


def _login_schwab(input: LoginRequest) -> BaseProvider:
    environ[SchwabProvider.API_KEY_ENV] = input.key
    environ[SchwabProvider.APP_SECRET_ENV] = input.secret
    pending = IN_APP_CONFIG.pending_schwab_response
    if pending and not schwab_context_is_live(pending):
        # its callback server died; the URL it handed out is worthless
        discard_schwab_context(pending)
        pending = None
    if pending and input.wait_for_external_auth:
        # the user has finished the external login - redeem the code that
        # this context's own callback server captured
        fetch_response(pending)
    elif pending:
        # a flow is already in flight. Its redirect server owns the callback
        # port, so minting a second context here would hand back a URL whose
        # redirect that context can never collect - the source of a hang
        # that only ends at callback_timeout. Re-offer the live one instead.
        raise SchwabExtraAuthenticationStepException(response=pending)
    else:
        context = create_login_context(api_key=input.key, app_secret=input.secret)
        if context:
            raise SchwabExtraAuthenticationStepException(response=context)

    provider = SchwabProvider(external_auth=True)
    IN_APP_CONFIG.pending_schwab_response = None
    return provider


def _login_etrade(input: LoginRequest) -> BaseProvider:
    environ[ETradeProvider.API_KEY_ENV] = input.key
    environ[ETradeProvider.API_SECRET_ENV] = input.secret
    sandbox = input.sandbox_enabled
    environ[ETradeProvider.SANDBOX_ENV] = "true" if sandbox else "false"
    pending = IN_APP_CONFIG.pending_etrade_response
    if pending and input.extra_factor:
        # the user pasted the verification code from the oob page
        etrade_complete_authorization(pending, str(input.extra_factor))
        IN_APP_CONFIG.pending_etrade_response = None
    elif pending:
        # a flow is in flight with no code supplied; the /public/etrade/callback
        # endpoint may have finished it for us (registered-callback mode)
        if not etrade_load_cached_token(sandbox):
            raise ETradeExtraAuthenticationStepException(response=pending)
        IN_APP_CONFIG.pending_etrade_response = None
    else:
        # reuses/renews a cached token when possible; otherwise hands back
        # an authorization URL for the user to visit
        context = etrade_create_login_context(input.key, input.secret, sandbox=sandbox)
        if context:
            raise ETradeExtraAuthenticationStepException(response=context)
    provider = ETradeProvider(external_auth=True, sandbox=sandbox)
    IN_APP_CONFIG.pending_etrade_response = None
    return provider


def _login_moomoo(input: LoginRequest) -> BaseProvider:
    environ[MooMooProvider.ACCOUNT_ENV] = input.key
    environ[MooMooProvider.PASSWORD_ENV] = input.secret
    if input.trading_pin:
        environ[MooMooProvider.TRADE_TOKEN_ENV] = input.trading_pin
    if input.proxy_path:
        environ[MooMooProvider.OPEND_ENV] = input.proxy_path

    # moomoo bills for quotes, so they are sourced from another logged in provider
    if not input.quote_provider:
        raise HTTPException(400, "No quote provider specified")
    quote_provider = IN_APP_CONFIG.provider_cache.get(input.quote_provider)
    if quote_provider is None:
        raise HTTPException(
            400, f"Quote provider {input.quote_provider.value} is not logged in"
        )
    provider = MooMooProvider(  # type: ignore
        proxy=MooMooProvider.Proxy(opend_path=input.proxy_path),
        quote_provider=quote_provider,
    )
    IN_APP_CONFIG.pending_momoo_response = None
    return provider


#: how each provider turns a LoginRequest into a live provider.
#:
#: Each entry owns only what is specific to that provider - the environment it
#: needs, its handshake, and clearing its own in-flight auth state. What every
#: successful login has in common lives in login() instead of being repeated
#: seven times, and the per-provider locals no longer share one scope.
PROVIDER_LOGINS: dict[ProviderType, Callable[[LoginRequest], BaseProvider]] = {
    ProviderType.ALPACA: _login_alpaca,
    ProviderType.ALPACA_PAPER: _login_alpaca_paper,
    ProviderType.ROBINHOOD: _login_robinhood,
    ProviderType.WEBULL: _login_webull,
    ProviderType.SCHWAB: _login_schwab,
    ProviderType.ETRADE: _login_etrade,
    ProviderType.MOOMOO: _login_moomoo,
}


def login(input: LoginRequest) -> bool:
    provider_login = PROVIDER_LOGINS.get(input.provider)
    if provider_login is None:
        raise HTTPException(404, "Selected provider not supported yet")
    # only reached when the handshake succeeded; a provider that needs another
    # step raises out of here rather than returning
    IN_APP_CONFIG.provider_cache[input.provider] = provider_login(input)
    IN_APP_CONFIG.logged_in = input.provider.value
    return True


@router.post("/login")
def login_handler(input: LoginRequest):
    # early exit if we have already logged in
    if not input.force and input.provider in IN_APP_CONFIG.provider_cache:
        return True
    try:
        return login(input)
    except SchwabExtraAuthenticationStepException as e:
        IN_APP_CONFIG.pending_schwab_response = e.response
        raise HTTPException(303, e.response.authorization_url)
    except ETradeExtraAuthenticationStepException as e:
        IN_APP_CONFIG.pending_etrade_response = e.response
        raise HTTPException(303, e.response.authorization_url)
    except ExtraAuthenticationStepException as e:
        IN_APP_CONFIG.pending_auth_response = e.response
        raise HTTPException(412, f"Additional authentication required: {e}")
    except HTTPException:
        raise
    except Exception as e:
        IN_APP_CONFIG.pending_auth_response = None
        raise HTTPException(400, f"Error logging in: {e}") from e


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


@dataclass
class SubPortfolioResult:
    """Outcome of touching one provider during a composite operation."""

    provider: ProviderType
    status: ProviderStatus
    duration: timedelta
    portfolio: RealPortfolio | None = None
    error: str | None = None
    refreshed_at: datetime | None = None


def seed_holding_cache(snapshots: list[ProviderSnapshot]) -> None:
    """Prime the holding cache from the client's own copy.

    The backend cache lives for one app session; the client keeps holdings on
    disk indefinitely. Replaying the client's copy is what lets a provider the
    user never logged into this session still count toward composite totals
    and purchase planning. Live data always wins - we only fill gaps.
    """
    for snapshot in snapshots:
        if snapshot.provider in IN_APP_CONFIG.holding_cache:
            continue
        IN_APP_CONFIG.holding_cache[snapshot.provider] = snapshot.to_portfolio()
        if snapshot.refreshed_at:
            IN_APP_CONFIG.holding_refreshed_at[snapshot.provider] = datetime.fromtimestamp(
                snapshot.refreshed_at, tz=UTC
            )


def cached_snapshot(key: ProviderType) -> RealPortfolio | None:
    """The last known holdings for a provider, detached from any live login.

    Detaching matters: a RealPortfolio still carrying a provider object is
    treated as an order destination by generate_composite_order_plan, and a
    provider whose login has since been dropped must not receive orders.
    """
    port = IN_APP_CONFIG.holding_cache.get(key)
    if port is None:
        return None
    if port.provider is not None and IN_APP_CONFIG.is_authenticated(key):
        return port
    return RealPortfolio(
        holdings=port.holdings,
        cash=port.cash,
        profit_and_loss=port.profit_and_loss,
        provider=None,
    )


def refresh_sub_portfolio(
    key: ProviderType, providers_to_refresh: list[ProviderType]
) -> SubPortfolioResult:
    """Fetch or recover one provider's holdings, never raising.

    Every failure mode degrades to the last known snapshot so that one
    unavailable provider cannot block an operation on the others.
    """
    start = datetime.now(UTC)
    item: BaseProvider | None = IN_APP_CONFIG.provider_cache.get(key, None)

    def elapsed() -> timedelta:
        return datetime.now(UTC) - start

    def fallback(status: ProviderStatus, error: str | None) -> SubPortfolioResult:
        return SubPortfolioResult(
            provider=key,
            status=status,
            duration=elapsed(),
            portfolio=cached_snapshot(key),
            error=error,
            refreshed_at=IN_APP_CONFIG.holding_refreshed_at.get(key),
        )

    if not item:
        return fallback(
            ProviderStatus.UNAUTHENTICATED,
            f"Not authenticated to {key.value}; showing last known holdings.",
        )
    if key not in providers_to_refresh:
        return fallback(ProviderStatus.CACHED, None)

    try:
        item.clear_cache(skip_clearing=["instrument_to_symbol_map"])
        rport = item.get_holdings()
        rport.profit_and_loss = item.get_profit_or_loss()
    except ConfigurationError as e:
        logger.exception(f"Auth error refreshing {key}, dropping login")
        IN_APP_CONFIG.drop_login(key)
        return fallback(ProviderStatus.UNAUTHENTICATED, str(e))
    except Exception as e:
        # exception() attaches the traceback, so it need not be formatted in
        logger.exception(f"Error refreshing {key}")
        return fallback(ProviderStatus.ERROR, str(e))

    now = datetime.now(tz=UTC)
    IN_APP_CONFIG.holding_cache[key] = rport
    IN_APP_CONFIG.holding_refreshed_at[key] = now
    return SubPortfolioResult(
        provider=key,
        status=ProviderStatus.REFRESHED,
        duration=elapsed(),
        portfolio=rport,
        refreshed_at=now,
    )


def sum_holdings(holdings: list[RealPortfolioElement]) -> Money:
    return Money(value=sum([x.value for x in holdings]))


def resolve_refresh_targets(
    input: CompositePortfolioRefreshRequest,
) -> list[ProviderType]:
    """Which providers to fetch live data for.

    Defaulting to "every provider we can actually reach" is what makes a
    partial refresh the no-argument behaviour.
    """
    if input.providers_to_refresh is None:
        return IN_APP_CONFIG.authenticated_subset(input.providers)
    return [p for p in input.providers_to_refresh if p in input.providers]


@router.post("/composite_portfolio/refresh")
def refresh_composite_portfolio(input: CompositePortfolioRefreshRequest):
    seed_holding_cache(input.cached)
    targets = resolve_refresh_targets(input)

    results: list[SubPortfolioResult] = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        portfolios = {
            executor.submit(refresh_sub_portfolio, key, targets)
            for key in input.providers
        }
        for future in as_completed(portfolios):
            results.append(future.result())

    if input.require_all:
        unauthenticated = [
            r.provider for r in results if r.status == ProviderStatus.UNAUTHENTICATED
        ]
        if unauthenticated:
            raise HTTPException(
                401,
                "Must log into "
                + ", ".join(p.value for p in unauthenticated)
                + " to refresh any element in this portfolio.",
            )
        failed = [r for r in results if r.status == ProviderStatus.ERROR]
        if failed:
            raise HTTPException(
                422, f"Error refreshing {failed[0].provider}: {failed[0].error}"
            )

    active: dict[str, RealPortfolioOutput] = {}
    raw: list[RealPortfolio] = []
    durations: dict[str, timedelta] = {}
    profit_and_loss = ProfitModel(
        appreciation=Money(value=0.0), dividends=Money(value=0.0)
    )
    investable = Money(value=0.0)

    for result in results:
        key = result.provider
        rport = result.portfolio
        durations[key] = result.duration
        holdings = rport.holdings if rport else []
        cash = rport.cash if rport else Money(value=0.0)
        pnl = rport.profit_and_loss if rport else None
        active[key] = RealPortfolioOutput(
            name=f"{key.name}",
            holdings=holdings,
            holding_size=sum_holdings(holdings),
            cash=cash,
            provider=key,
            profit_or_loss_v2=pnl,
            profit_or_loss=pnl.total if pnl else None,
            status=result.status,
            error=result.error,
            refreshed_at=(
                int(result.refreshed_at.timestamp()) if result.refreshed_at else None
            ),
        )
        if pnl:
            profit_and_loss += pnl
        if rport:
            raw.append(rport)
            if result.status not in UNUSABLE_STATUSES and cash:
                investable += max(cash, Money(value=0.0))

    active = {k: active[k] for k in sorted(active.keys(), key=lambda x: active[x].holding_size.value if active[x].holding_size is not None else 0.0, reverse=True)}  # type: ignore
    internal = CompositePortfolio(raw)
    degraded = [r.provider for r in results if r.status in UNUSABLE_STATUSES]

    return CompositePortfolioOutput(
        name=input.key,
        holdings=internal.holdings,
        cash=internal.cash,
        investable_cash=investable,
        refresh_time=durations,
        components=active,
        refreshed_at=int(datetime.now(tz=UTC).timestamp()),
        profit_or_loss_v2=profit_and_loss,
        profit_or_loss=profit_and_loss.total,
        partial=bool(degraded),
        degraded_providers=degraded,
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
    seed_holding_cache(input.cached)
    children: list[RealPortfolio] = []
    buy_orders: dict[ProviderType, PurchaseStrategy] = {}
    skipped: list[ProviderType] = []

    for provider in input.providers:
        if not IN_APP_CONFIG.is_authenticated(provider):
            # holdings still shape the plan - they are part of the portfolio we
            # are trying to reach the target allocation for - but no orders can
            # be routed here, so the provider stays out of buy_orders.
            snapshot = cached_snapshot(provider)
            if snapshot:
                children.append(snapshot)
            skipped.append(provider)
            continue
        try:
            iprovider = get_provider_safe(provider)
            sub_port = IN_APP_CONFIG.holding_cache.get(provider)
            if sub_port is None or sub_port.provider is None:
                # a snapshot seeded from the client has no live provider
                # attached, so it cannot be used as an order destination
                sub_port = iprovider.get_holdings()
                IN_APP_CONFIG.holding_cache[provider] = sub_port
                IN_APP_CONFIG.holding_refreshed_at[provider] = datetime.now(tz=UTC)
            buy_orders[provider] = input.purchase_strategy
            children.append(sub_port)
        except ConfigurationError:
            IN_APP_CONFIG.drop_login(provider)
            if input.require_all:
                raise
            snapshot = cached_snapshot(provider)
            if snapshot:
                children.append(snapshot)
            skipped.append(provider)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                500, f"Error planning composite purchase: {e} on provider {provider}"
            ) from e

    if skipped and input.require_all:
        raise HTTPException(
            401,
            "Not authenticated to " + ", ".join(p.value for p in skipped),
        )
    if not buy_orders:
        raise HTTPException(
            401,
            "Authenticate to at least one provider in this portfolio to plan a purchase.",
        )
    if input.provider and input.provider not in buy_orders:
        # reweighting needs a provider to price against; prefer one we can reach
        input = input.model_copy(update={"provider": None})

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
    return PurchaseOrderOutput(
        to_buy=final,
        skipped_providers=skipped,
        order_providers=list(buy_orders.keys()),
    )


@router.post("/plan_composite_purchase")
def plan_composite_purchase(input: BuyRequest):
    try:
        return _plan_composite_purchase(input)
    except ConfigurationError:
        raise
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error planning composite purchase: {e}") from e


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
    orders: list[OrderItem], provider: BaseProvider, stale_providers: set[ProviderType]
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
            logger.exception(f"Unexpected failure placing order for {order.ticker}")
            order.status = OrderStatus.FAILED
            order.message = str(e)
            output.append(order)
    return output


@router.post("/buy_index_from_plan_multi_provider")
def buy_index_from_plan_multi_provider(input: BuyRequestFinalMultiProvider):
    output: list[OrderItem] = []
    stale_providers: set[ProviderType] = set()
    grouped = defaultdict(list)
    for order in input.plan.to_buy:
        grouped[order.provider].append(order)

    missing = [key for key in grouped if not IN_APP_CONFIG.is_authenticated(key)]
    if missing and input.require_all:
        raise HTTPException(
            401,
            "Not logged in to " + ", ".join(p.value for p in missing),
        )
    if missing and len(missing) == len(grouped):
        raise HTTPException(
            401,
            "Not logged in to any provider with orders to place: "
            + ", ".join(p.value for p in missing),
        )
    # orders bound for a provider we cannot reach fail individually; the rest
    # of the plan still executes
    for key in missing:
        for order in grouped.pop(key):
            order.status = OrderStatus.FAILED
            order.message = f"Not authenticated to {key.value}; order skipped."
            output.append(order)

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(
                place_orders,
                orders,
                IN_APP_CONFIG.provider_cache[key],
                stale_providers,
            )
            for key, orders in grouped.items()
        }
        for future in as_completed(futures):
            output += future.result()
    for provider in stale_providers:
        IN_APP_CONFIG.drop_login(provider)
    return BuyRequestFinalMultiProviderOutput(orders=output, skipped_providers=missing)


# Add the endpoint to the router
@router.post("/database/export_portfolio_database")
def export_portfolio_database(input: DatabaseExportRequest):
    """
    Export portfolio data to a DuckDB database.
    Database will be stored at ~/.fundiverse/databases/{portfolio_name}.db
    """
    try:
        return export_portfolio_to_database(input, IN_APP_CONFIG)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error exporting portfolio database: {e}") from e


# Add endpoint to get database info
@router.get("/database_info/{portfolio_name}")
def get_database_info(portfolio_name: str):
    """Get information about an existing portfolio database"""
    db_path = get_database_path(portfolio_name)

    if not db_path.exists():
        raise HTTPException(404, f"No database found for portfolio '{portfolio_name}'")
    db = None
    try:
        db = DuckDBDatastore(str(db_path))

        # Query for basic stats
        holdings_row = db.query("SELECT holdings.symbol.id.count;").fetchone()
        holdings_count = holdings_row[0] if holdings_row else 0
        dividends_row = db.query("SELECT dividend.id.count;").fetchone()
        dividends_count = dividends_row[0] if dividends_row else 0
        providers = db.query("SELECT provider.name;").fetchall()

        return {
            "database_path": str(db_path),
            "portfolio_name": portfolio_name,
            "exists": True,
            "total_holdings": holdings_count,
            "total_dividends": dividends_count,
            "providers": [p[0] for p in providers],
            "file_size_mb": db_path.stat().st_size / (1024 * 1024),
        }
    except Exception as e:
        raise HTTPException(500, f"Error reading database info: {e}") from e
    finally:
        if db:
            db.close()


# Add endpoint to download the database file
@router.get("/database/download/{portfolio_name}")
def download_database(portfolio_name: str):
    """Download the portfolio database file for use in DuckDB WASM"""
    db_path = get_database_path(portfolio_name)

    if not db_path.exists():
        raise HTTPException(404, f"No database found for portfolio '{portfolio_name}'")
    db = None
    try:
        # Open connection, checkpoint, and close
        db = DuckDBDatastore(str(db_path))
        db.executor.execute_raw_sql(
            "CHECKPOINT;"
        )  # This writes all WAL data to the main file
        db.close()
        db = None

        # Small delay to ensure file system sync
        # Read entire file into memory
        file_content = db_path.read_bytes()

        from fastapi.responses import Response

        return Response(
            content=file_content,
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f'attachment; filename="{portfolio_name}.db"',
                "Access-Control-Expose-Headers": "Content-Disposition",
            },
        )
    except Exception as e:
        raise HTTPException(500, f"Error downloading database: {e}") from e
    finally:
        if db:
            db.close()


# Add endpoint to delete a database
@router.delete("/database/{portfolio_name}")
def delete_database(portfolio_name: str):
    """Delete a portfolio database"""
    db_path = get_database_path(portfolio_name)

    if not db_path.exists():
        raise HTTPException(404, f"No database found for portfolio '{portfolio_name}'")

    try:
        db_path.unlink()
        return {"deleted": True, "portfolio_name": portfolio_name}
    except Exception as e:
        raise HTTPException(500, f"Error deleting database: {e}") from e


@router.get("/trilogy_model")
def trilogy_model():
    from py_portfolio_index.datastores.base_datastore import BaseDatastore

    files: dict[str, str] = BaseDatastore.get_files_and_contents()
    return files


class SleepRequest(BaseModel):
    sleep: int


@router.post("/long_sleep")
def long_sleep(sleep: SleepRequest):
    import time

    time.sleep(sleep.sleep)
    return {"slept": sleep.sleep}


async def exit_app():
    for task in asyncio.all_tasks():
        print(f"cancelling task: {task}")
        try:
            task.cancel()
        except Exception:
            logger.exception(f"Failed to cancel task {task}")
    asyncio.gather(*asyncio.all_tasks())
    loop = asyncio.get_running_loop()
    loop.stop()
    raise ShutdownException("Server is shutting down")


## Build async routes
router_routes = list(router.routes)
for path in router_routes:
    if not isinstance(path, APIRoute):
        continue
    if path.methods and "POST" in path.methods:

        def make_function(endpoint):
            args = get_type_hints(endpoint)

            async def dynamic_route_handler(
                background_tasks: BackgroundTasks,
                arg: Annotated[Any, Body()] = None,
            ):
                guid = str(uuid.uuid4())
                arg_model: BaseModel = next(iter(args.values()))
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

## Public (unauthenticated) endpoints, mounted as a sub-app so they bypass the
## bearer-token dependency. OAuth redirect callbacks arrive from the user's
## browser, which does not carry our auth header.
public_app = FastAPI()


def _callback_page(message: str, detail: str, status_code: int = 200) -> HTMLResponse:
    return HTMLResponse(
        f"<html><body><h3>{message}</h3><p>{detail}</p></body></html>",
        status_code=status_code,
    )


@public_app.get("/etrade/callback")
async def etrade_oauth_callback(oauth_verifier: str = "", oauth_token: str = ""):
    """Complete a pending E*TRADE authorization from a callback redirect.

    E*TRADE only redirects here once their API support team has registered
    this URL (http://localhost:3042/public/etrade/callback) for the consumer
    key. Until then, the oob flow applies: the user pastes the verification
    code into the login form as the extra factor instead.
    """
    pending = IN_APP_CONFIG.pending_etrade_response
    if not pending:
        return _callback_page(
            "No E*TRADE authorization is in progress.",
            "Start a login from Fundiverse first.",
            status_code=404,
        )
    if not oauth_verifier:
        return _callback_page(
            "E*TRADE did not supply a verification code.",
            "The redirect was missing the oauth_verifier parameter.",
            status_code=400,
        )
    try:
        etrade_complete_authorization(pending, oauth_verifier)
    except Exception as e:
        logger.exception("E*TRADE callback failed")
        return _callback_page(
            "E*TRADE authorization failed.", str(e), status_code=400
        )
    IN_APP_CONFIG.pending_etrade_response = None
    return _callback_page(
        "E*TRADE authorization complete.",
        "You may close this window, return to Fundiverse, and click Authenticate again.",
    )


app.mount("/public", public_app)


def run():
    LOGGING_CONFIG["disable_existing_loggers"] = True
    import sys

    if os.environ.get("IN_CI"):
        assert all(
            x in AVAILABLE_PROVIDERS
            for x in [
                ProviderType.MOOMOO,
                ProviderType.ROBINHOOD,
                ProviderType.WEBULL,
                ProviderType.SCHWAB,
                ProviderType.ETRADE,
                ProviderType.ALPACA,
                ProviderType.ALPACA_PAPER,
            ]
        )
        print("Running in a unit test, exiting")
        sys.exit(0)
    elif getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        print("running in a PyInstaller bundle, sending stdout to devnull")
        with open(os.devnull, "w") as devnull:
            sys.stdout = devnull
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
    except Exception:
        logger.exception("Server is shutting down due to an unhandled error")
        sys.exit(1)


if __name__ == "__main__":
    multiprocessing.freeze_support()
    run()
