from collections.abc import Callable
from typing import Any

import dotenv

dotenv.load_dotenv()
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from logging import getLogger

from fastapi import (
    HTTPException,
)
from py_portfolio_index.enums import ProviderType
from py_portfolio_index.models import (
    LoginResponse,
    RealPortfolio,
)
from py_portfolio_index.portfolio_providers.base_portfolio import BaseProvider
from py_portfolio_index.portfolio_providers.helpers.etrade import (
    ETradeAuthContext,
)
from py_portfolio_index.portfolio_providers.helpers.schwab import (
    SchwabAuthContext,
)
from pytz import UTC


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
    provider_cache: dict[ProviderType, BaseProvider] = field(default_factory=dict)
    holding_cache: dict[ProviderType, RealPortfolio] = field(default_factory=dict)
    # when each entry in holding_cache was last known to be accurate. Entries
    # seeded from a client-held cache carry the client's timestamp, so the UI
    # can show how stale a partially-refreshed portfolio is per provider.
    holding_refreshed_at: dict[ProviderType, datetime] = field(default_factory=dict)
    pending_auth_response: LoginResponse | None = None
    pending_schwab_response: SchwabAuthContext | None = None
    pending_etrade_response: ETradeAuthContext | None = None
    pending_momoo_response: str | None = None
    auth_token: str | None = None
    validate: bool = False
    background_tasks: dict[str, AsyncTask] = field(default_factory=dict)

    def is_authenticated(self, provider: ProviderType) -> bool:
        return provider in self.provider_cache

    def authenticated_subset(self, providers) -> list[ProviderType]:
        return [p for p in providers if p in self.provider_cache]

    def drop_login(self, provider: ProviderType) -> None:
        """Forget a login without discarding the holdings we already fetched -
        stale data is still useful for planning against the rest of a
        partially authenticated portfolio."""
        self.provider_cache.pop(provider, None)

    @property
    def default_provider(self):
        # get the fastest provider
        priority = [
            ProviderType.ALPACA,
            ProviderType.ROBINHOOD,
            ProviderType.WEBULL,
            ProviderType.SCHWAB,
            ProviderType.ETRADE,
            ProviderType.MOOMOO,
            ProviderType.ALPACA_PAPER,
        ]
        for provider in priority:
            if provider in self.provider_cache:
                return provider
        if self.provider_cache:
            return next(iter(self.provider_cache))
        raise HTTPException(401, "No logged in provider specified")


logger = getLogger(__name__)


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
        # the task result carries the error to its caller, but nothing else
        # would ever surface the traceback of a background failure
        logger.exception(f"Background task {guid} failed")
        task.error = e
        task.status = BackgroundStatus.FAILED
    config.background_tasks[guid] = task
