"""The database export follows the same partial rule as the rest of the app.

It runs against whatever is authenticated instead of refusing to export
anything until every provider in the portfolio is reachable.
"""

import pytest
from fastapi.testclient import TestClient
from py_portfolio_index.enums import ProviderType
from py_portfolio_index.exceptions import ConfigurationError
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


@pytest.mark.parametrize("provider", [ProviderType.SCHWAB, ProviderType.ETRADE])
def test_repeat_export_with_unknown_ticker(
    test_client: TestClient, tmp_path, monkeypatch, provider: ProviderType
):
    """Unrecognized tickers pool into one '???' row per provider; exporting
    twice must replace that row rather than collide on the primary key, and
    positions sold between exports must not linger."""
    monkeypatch.setattr(
        exports, "get_database_path", lambda name: tmp_path / f"{name}.db"
    )
    active = test_client.app.in_app_config  # type: ignore
    active.provider_cache.clear()
    active.holding_cache.clear()
    active.provider_cache[provider] = FakeProvider(
        provider,
        holdings=[holding("AAPL", 100), holding("NOTAREALTICKERX", 50)],
    )
    try:
        body = {"portfolio_name": "dup-port", "providers": [provider.value]}
        first = test_client.post("/database/export_portfolio_database", json=body)
        assert first.status_code == 200, first.text

        active.provider_cache[provider] = FakeProvider(
            provider, holdings=[holding("NOTAREALTICKERX", 75)]
        )
        second = test_client.post("/database/export_portfolio_database", json=body)
        assert second.status_code == 200, second.text

        db = exports.DuckDBDatastore(str(tmp_path / "dup-port.db"))
        try:
            rows = db.executor.execute_raw_sql(
                "SELECT symbol, value FROM ticker_holdings ORDER BY symbol;"
            ).fetchall()
        finally:
            db.close()
        assert rows == [(-1, 75.0)]
    finally:
        active.provider_cache.clear()
        active.holding_cache.clear()


class ExpiredDividendsProvider(FakeProvider):
    """Holdings come from the cache; the dividend fetch finds the login gone,
    as E*TRADE does once its daily token lapses."""

    def get_dividend_details(self, start=None):
        raise ConfigurationError("E*TRADE API returned 401: token_rejected")


def test_export_survives_a_login_expiring_mid_export(test_client, export_env):
    config, created = export_env
    config.provider_cache[ProviderType.ALPACA] = FakeProvider(
        ProviderType.ALPACA, holdings=[holding("AAPL", 100)]
    )
    config.provider_cache[ProviderType.ETRADE] = ExpiredDividendsProvider(
        ProviderType.ETRADE, holdings=[holding("MSFT", 50)]
    )

    response = export(test_client, providers=["alpaca", "etrade"])
    assert response.status_code == 200, response.text
    data = response.json()
    # holdings already written for etrade are kept; its login is forgotten
    assert data["providers_processed"] == ["alpaca", "etrade"]
    assert "token_rejected" in data["provider_errors"]["etrade"]
    assert ProviderType.ETRADE not in config.provider_cache
    assert ProviderType.ETRADE in created[0].holdings_by_provider


def test_export_bundles_the_target_composition(
    test_client: TestClient, tmp_path, monkeypatch
):
    import io
    import json
    import zipfile

    import main

    monkeypatch.setattr(
        exports, "get_database_path", lambda name: tmp_path / f"{name}.db"
    )
    monkeypatch.setattr(main, "get_database_path", lambda name: tmp_path / f"{name}.db")
    active = test_client.app.in_app_config  # type: ignore
    active.provider_cache.clear()
    active.holding_cache.clear()
    active.provider_cache[ProviderType.ALPACA] = FakeProvider(
        ProviderType.ALPACA, holdings=[holding("AAPL", 100)]
    )
    try:
        body = {
            "portfolio_name": "bundle-port",
            "providers": ["alpaca"],
            "composition": {
                "index": "large_cap",
                "target_size": 10000,
                "stock_exclusions": ["AAPL"],
            },
        }
        response = test_client.post("/database/export_portfolio_database", json=body)
        assert response.status_code == 200, response.text
        assert response.json()["composition_included"] is True

        db = exports.DuckDBDatastore(str(tmp_path / "bundle-port.db"))
        try:
            run = db.executor.execute_raw_sql
            targets = dict(
                run("SELECT ticker, target_value FROM target_holdings;").fetchall()
            )
            index_name = run("SELECT index_name FROM portfolio_composition;").fetchone()
        finally:
            db.close()
        assert "AAPL" not in targets
        assert sum(targets.values()) == pytest.approx(10000)
        assert index_name == ("large_cap",)

        bundle = test_client.get("/database/download_bundle/bundle-port")
        assert bundle.status_code == 200
        with zipfile.ZipFile(io.BytesIO(bundle.content)) as archive:
            assert set(archive.namelist()) == {"bundle-port.db", "composition.json"}
            document = json.loads(archive.read("composition.json"))
        assert document["customizations"]["stock_exclusions"] == ["AAPL"]
        assert len(document["targets"]) == len(targets)
    finally:
        active.provider_cache.clear()
        active.holding_cache.clear()
