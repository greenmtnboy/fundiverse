from typing import List, Any


from pathlib import Path
from py_portfolio_index.datastores.duckdb_datastore import DuckDBDatastore
from py_portfolio_index.enums import ObjectKey

from fastapi import (
    HTTPException,
)

from py_portfolio_index.enums import ProviderType


from pydantic import BaseModel
from config import ActiveConfig

class DatabaseExportRequest(BaseModel):
    portfolio_name: str
    providers: List[ProviderType]
    force_reset: bool = False


class DatabaseExportResponse(BaseModel):
    database_path: str
    portfolio_name: str
    providers_processed: List[ProviderType]
    total_holdings: int
    total_dividends: int


# Add helper function to get database path
def get_database_path(portfolio_name: str) -> Path:
    """Get canonical storage location for portfolio database"""
    db_dir = Path.home() / ".fundiverse" / "databases"
    db_dir.mkdir(parents=True, exist_ok=True)
    return db_dir / f"{portfolio_name}.db"


def export_portfolio_to_database(
    input: DatabaseExportRequest, config: ActiveConfig
) -> DatabaseExportResponse:
    """Export portfolio data to a DuckDB database"""
    db_path = get_database_path(input.portfolio_name)

    # Initialize database
    db = DuckDBDatastore(str(db_path))
    stage = 'init'
    try:
        # Initialize tickers table
        db.intialize_tickers()

        # Reset database if requested or if it's new
        if input.force_reset or not db_path.exists():
            db.reset()

        total_holdings = 0
        total_dividends = 0
        providers_processed = []

        # Process each provider
        for provider_type in input.providers:
            stage = f'provider {provider_type}'
            # Get provider instance
            provider = config.provider_cache.get(provider_type)
            # Get holdings
            holdings = config.holding_cache.get(
                provider_type, provider.get_holdings()
            )


            # Persist holdings
            db.persist_holding_data(holdings.holdings, provider_type)
            total_holdings += len(holdings.holdings)

            # Get dividend watermarks
            min_dividends, max_dividends = db.get_watermarks(
                provider_type=provider_type, object_key=ObjectKey.DIVIDENDS
            )

            # Get and persist dividends
            dividends = provider.get_dividend_details(start=max_dividends)
            db.persist_dividend_data(dividends)
            total_dividends += len(dividends)

            providers_processed.append(provider_type)

        db.close()

        return DatabaseExportResponse(
            database_path=str(db_path),
            portfolio_name=input.portfolio_name,
            providers_processed=providers_processed,
            total_holdings=total_holdings,
            total_dividends=total_dividends,
        )

    except Exception as e:
        db.close()
        raise HTTPException(500, f"Error exporting portfolio to database in {stage}: {e}")
