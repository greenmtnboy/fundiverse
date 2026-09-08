"""The database export follows the same partial rule as the rest of the app.

It runs against whatever is authenticated instead of refusing to export
anything until every provider in the portfolio is reachable.
"""

import pytest
from fastapi.testclient import TestClient
from py_portfolio_index.enums import ProviderType
from test_partial_auth import FakeProvider, holding

import exports


class FakeDatastore:
    """Stands in for DuckDBDatastore so tests touch no real database."""

    def __init__(self, path):
        self.path = path
        self.holdings_by_provider = {}
        self.closed = 0

    def intialize_tickers(self):
        return None

    def reset(self):
        return None

    def persist_holding_data(self, holdings, provider_type):
        self.holdings_by_provider[provider_type] = holdings

    def get_watermarks(self, provider_type, object_key):
        return None, None

    def persist_dividend_data(self, dividends):
        return None

    def close(self):
        self.closed += 1


@pytest.fixture
def export_env(test_client: TestClient, tmp_path, monkeypatch):
    """Isolate the export from the user's real ~/.fundiverse directory."""
    created = []

    def make_db(path):
        db = FakeDatastore(path)
        created.append(db)
        return db

    monkeypatch.setattr(exports, "DuckDBDatastore", make_db)
    monkeypatch.setattr(
        exports, "get_database_path", lambda name: tmp_path / f"{name}.db"
    )

    active = test_client.app.in_app_config  # type: ignore
    active.provider_cache.clear()
    active.holding_cache.clear()
    active.holding_refreshed_at.clear()
    yield active, created
    active.provider_cache.clear()
    active.holding_cache.clear()
    active.holding_refreshed_at.clear()


def export(test_client: TestClient, **overrides):
    body = {"portfolio_name": "ci-port", "providers": ["alpaca", "robinhood"]}
    body.update(overrides)
    return test_client.post("/database/export_portfolio_database", json=body)


def test_export_skips_unauthenticated_providers(test_client, export_env):
    config, _ = export_env
    config.provider_cache[ProviderType.ALPACA] = FakeProvider(
        ProviderType.ALPACA, holdings=[holding("AAPL", 100)]
    )

    response = export(test_client)
    assert response.status_code == 200
    data = response.json()
    assert data["providers_processed"] == ["alpaca"]
    assert data["providers_skipped"] == ["robinhood"]
    assert data["total_holdings"] == 1


def test_export_require_all_rejects_partial(test_client, export_env):
    config, _ = export_env
    config.provider_cache[ProviderType.ALPACA] = FakeProvider(
        ProviderType.ALPACA, holdings=[holding("AAPL", 100)]
    )

    response = export(test_client, require_all=True)
    assert response.status_code == 400
    assert "robinhood" in response.json()["detail"]


def test_export_fails_when_nothing_is_authenticated(test_client, export_env):
    response = export(test_client)
    # a 401 rather than an empty success, so the UI prompts for a login
    assert response.status_code == 401
    assert "alpaca" in response.json()["detail"]


def test_export_closes_the_database_on_failure(test_client, export_env):
    _, created = export_env
    export(test_client)
    assert created and all(db.closed for db in created)
