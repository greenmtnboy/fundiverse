from typing import Annotated, Any, Callable, Dict, List, Optional

import dotenv

dotenv.load_dotenv()
import asyncio
import multiprocessing
import os
import sys
import traceback
import uuid
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import asynccontextmanager
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from logging import StreamHandler, getLogger
from os import environ
from typing import get_type_hints
from pathlib import Path
from py_portfolio_index.datastores.duckdb_datastore import DuckDBDatastore
from py_portfolio_index.enums import ObjectKey
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
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.routing import APIRoute
from fastapi.security import OAuth2PasswordBearer
from py_portfolio_index import (
    AVAILABLE_PROVIDERS,
    INDEXES,
    STOCK_LISTS,
    AlpacaProvider,
    Logger,
    MooMooProvider,
    PaperAlpacaProvider,
    PurchaseStrategy,
    RobinhoodProvider,
    SchwabProvider,
    WebullPaperProvider,
    WebullProvider,
    generate_composite_order_plan,
)
from py_portfolio_index.enums import ProviderType
from py_portfolio_index.exceptions import (
    ConfigurationError,
    ExtraAuthenticationStepException,
    OrderError,
)
from py_portfolio_index.models import (
    CompositePortfolio,
    IdealPortfolio,
    LoginResponse,
    Money,
    OrderElement,
    OrderPlan,
    OrderType,
    ProfitModel,
    RealPortfolio,
    RealPortfolioElement,
)
from py_portfolio_index.portfolio_providers.base_portfolio import BaseProvider
from py_portfolio_index.portfolio_providers.helpers.robinhood import (
    login as rh_login,
)
from py_portfolio_index.portfolio_providers.helpers.schwab import (
    SchwabAuthContext,
    create_login_context,
    fetch_response,
)
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from pytz import UTC
from starlette.background import BackgroundTask
from uvicorn.config import LOGGING_CONFIG


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
            ProviderType.MOOMOO,
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
