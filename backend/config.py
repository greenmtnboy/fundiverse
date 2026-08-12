from typing import Any, Callable, Dict

import dotenv

dotenv.load_dotenv()
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

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
    provider_cache: Dict[ProviderType, BaseProvider] = field(default_factory=dict)
    holding_cache: Dict[ProviderType, RealPortfolio] = field(default_factory=dict)
    pending_auth_response: LoginResponse | None = None
    pending_schwab_response: SchwabAuthContext | None = None
    pending_etrade_response: ETradeAuthContext | None = None
    pending_momoo_response: str | None = None
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
            ProviderType.ETRADE,
            ProviderType.MOOMOO,
            ProviderType.ALPACA_PAPER,
        ]
        for provider in priority:
            for key, _ in self.provider_cache.items():
                if key == provider:
                    return key
        if self.provider_cache:
            return list(self.provider_cache.keys())[0]
        raise HTTPException(401, "No logged in provider specified")


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
