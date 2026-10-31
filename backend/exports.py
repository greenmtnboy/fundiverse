import json
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import (
    HTTPException,
)
from py_portfolio_index.datastores.duckdb_datastore import DuckDBDatastore
from py_portfolio_index.enums import ObjectKey, ProviderType
from py_portfolio_index.exceptions import ConfigurationError
from pydantic import BaseModel, Field

from config import ActiveConfig


class PortfolioComposition(BaseModel):
    """The portfolio's target as the user configured it: the index plus every
    customization, so an export can be compared against what we aim for."""

    index: str | None = None
    target_size: float | None = None
    reweight: bool = False
    stock_exclusions: list[str] = Field(default_factory=list)
    list_exclusions: list[str] = Field(default_factory=list)
    stock_modifications: list[dict[str, Any]] = Field(default_factory=list)
    list_modifications: list[dict[str, Any]] = Field(default_factory=list)


class DatabaseExportRequest(BaseModel):
    portfolio_name: str
    providers: list[ProviderType] = Field(default_factory = list)
    force_reset: bool = False
    require_all: bool = False
    composition: PortfolioComposition | None = None


class DatabaseExportResponse(BaseModel):
    database_path: str
    portfolio_name: str
    providers_processed: list[ProviderType]
    total_holdings: int
    total_dividends: int
    #: providers left out because we are not authenticated to them
    providers_skipped: list[ProviderType] = Field(default_factory=list)
    #: providers whose login went stale mid-export; whatever we had already
    #: written for them (usually cached holdings) is kept
    provider_errors: dict[ProviderType, str] = Field(default_factory=dict)
    composition_included: bool = False
    #: why the customized target couldn't be resolved, if it couldn't
    composition_error: str | None = None


# Add helper function to get database path
def get_database_path(portfolio_name: str) -> Path:
    """Get canonical storage location for portfolio database"""
    db_dir = Path.home() / ".fundiverse" / "databases"
    db_dir.mkdir(parents=True, exist_ok=True)
    return db_dir / f"{portfolio_name}.db"


def get_composition_path(portfolio_name: str) -> Path:
    """Sidecar JSON with the target composition, bundled next to the database"""
    return get_database_path(portfolio_name).with_suffix(".composition.json")


#: resolves a composition into its customized (ticker, weight) target
TargetResolver = Callable[["PortfolioComposition"], list[tuple[str, float]]]


def persist_composition(
    db: DuckDBDatastore,
    portfolio_name: str,
    composition: PortfolioComposition,
    targets: list[tuple[str, float]],
    target_error: str | None,
) -> dict[str, Any]:
    """Write the target into the database and return it as a JSON document.

    target_value uses the portfolio's target size, so "how far off am I" is a
    join between target_holdings and ticker_holdings."""
    exported_at = datetime.now(UTC).isoformat()
    size = composition.target_size or 0.0
    run = db.executor.execute_raw_sql
    run(
        "CREATE OR REPLACE TABLE target_holdings ("
        "ticker VARCHAR PRIMARY KEY, weight DOUBLE, target_value DOUBLE);"
    )
    for ticker, weight in targets:
        run(
            "INSERT INTO target_holdings VALUES (:ticker, :weight, :target_value);",
            {"ticker": ticker, "weight": weight, "target_value": weight * size},
        )
    customizations = composition.model_dump(exclude={"index", "target_size"})
    run(
        "CREATE OR REPLACE TABLE portfolio_composition ("
        "portfolio_name VARCHAR, index_name VARCHAR, target_size DOUBLE, "
        "customizations JSON, target_error VARCHAR, exported_at TIMESTAMPTZ);"
    )
    run(
        "INSERT INTO portfolio_composition VALUES "
        "(:name, :index, :size, :customizations, :error, :exported_at);",
        {
            "name": portfolio_name,
            "index": composition.index,
            "size": composition.target_size,
            "customizations": json.dumps(customizations),
            "error": target_error,
            "exported_at": exported_at,
        },
    )
    db.executor.connection.commit()
    return {
        "portfolio_name": portfolio_name,
        "exported_at": exported_at,
        "index": composition.index,
        "target_size": composition.target_size,
        "customizations": customizations,
        "target_error": target_error,
        "targets": [
            {"ticker": t, "weight": w, "target_value": w * size} for t, w in targets
        ],
    }


def export_portfolio_to_database(
    input: DatabaseExportRequest,
    config: ActiveConfig,
    resolve_target: TargetResolver | None = None,
) -> DatabaseExportResponse:
    """Export portfolio data to a DuckDB database"""
    db_path = get_database_path(input.portfolio_name)

    # Initialize database
    db = DuckDBDatastore(str(db_path))
    stage = 'init'
    providers = input.providers
    if not providers:
        providers = list(config.holding_cache.keys())
    try:
        # Initialize tickers table
        db.intialize_tickers()

        # Reset database if requested or if it's new
        if input.force_reset or not db_path.exists():
            db.reset()

        total_holdings = 0
        total_dividends = 0
        providers_processed = []
        providers_skipped = []
        provider_errors: dict[ProviderType, str] = {}

        # Process each provider
        for provider_type in providers:
            stage = f'provider {provider_type}'
            # Get provider instance
            provider = config.provider_cache.get(provider_type)
            if provider is None:
                # exports run against whatever is authenticated; an
                # unreachable provider is skipped rather than failing the
                # export for every other provider
                if input.require_all:
                    raise HTTPException(status_code=400, detail=f"Provider {provider_type.value} not configured")
                providers_skipped.append(provider_type)
                continue
            holdings_written = False
            try:
                # Get holdings
                holdings = config.holding_cache.get(provider_type)
                if holdings is None:
                    holdings = provider.get_holdings()

                # Persist holdings; each call replaces the provider's previous snapshot
                db.persist_holding_data(holdings.holdings, provider_type)
                total_holdings += len(holdings.holdings)
                holdings_written = True

                # Get dividend watermarks
                _min_dividends, max_dividends = db.get_watermarks(
                    provider_type=provider_type, object_key=ObjectKey.DIVIDENDS
                )

                # Get and persist dividends; some providers (webull) have no
                # dividend endpoint at all, so export holdings for them regardless
                try:
                    dividends = provider.get_dividend_details(start=max_dividends)
                except NotImplementedError:
                    dividends = []
                db.persist_dividend_data(dividends)
                total_dividends += len(dividends)
            except ConfigurationError as e:
                # a login that expired since we cached its holdings (E*TRADE
                # tokens lapse daily); forget it so the UI asks to log in
                # again, and keep exporting everyone else
                config.drop_login(provider_type)
                provider_errors[provider_type] = str(e)
                if not holdings_written:
                    providers_skipped.append(provider_type)
                    continue

            providers_processed.append(provider_type)

        if not providers_processed and providers_skipped:
            raise HTTPException(
                401,
                "Not authenticated to any provider in this portfolio: "
                + ", ".join(p.value for p in providers_skipped),
            )

        composition_included = False
        composition_error = None
        composition_path = get_composition_path(input.portfolio_name)
        if input.composition:
            stage = 'composition'
            targets: list[tuple[str, float]] = []
            if not input.composition.index:
                composition_error = "No target index selected"
            elif resolve_target is None:
                composition_error = "Target resolution unavailable"
            else:
                try:
                    targets = resolve_target(input.composition)
                except (HTTPException, ConfigurationError, KeyError, ValueError) as e:
                    # e.g. reweighting needs a live provider to price against;
                    # the holdings are still worth exporting without targets
                    composition_error = getattr(e, "detail", None) or str(e)
            document = persist_composition(
                db, input.portfolio_name, input.composition, targets, composition_error
            )
            composition_path.write_text(json.dumps(document, indent=2), encoding="utf-8")
            composition_included = bool(targets)
        else:
            # don't bundle a stale composition from an earlier export
            composition_path.unlink(missing_ok=True)

        db.close()

        return DatabaseExportResponse(
            database_path=str(db_path),
            portfolio_name=input.portfolio_name,
            providers_processed=providers_processed,
            total_holdings=total_holdings,
            total_dividends=total_dividends,
            providers_skipped=providers_skipped,
            provider_errors=provider_errors,
            composition_included=composition_included,
            composition_error=composition_error,
        )

    except HTTPException:
        # auth/config problems already carry the right status code; don't
        # relabel them as a 500
        db.close()
        raise
    except Exception as e:
        db.close()
        raise HTTPException(
            500, f"Error exporting portfolio to database in {stage}: {e}"
        ) from e
