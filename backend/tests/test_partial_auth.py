"""Coverage for the partially-authenticated portfolio model.

The premise: an operation touching several providers should do as much as it
can with whatever the user is logged into, rather than failing until every
provider is authenticated.
"""

from decimal import Decimal
from typing import Dict, List, Optional, Set

import pytest
from fastapi.testclient import TestClient
from py_portfolio_index.enums import ProviderType
from py_portfolio_index.exceptions import ConfigurationError, OrderError
from py_portfolio_index.models import (
    Money,
    ProfitModel,
    RealPortfolio,
    RealPortfolioElement,
)
from py_portfolio_index.portfolio_providers.base_portfolio import BaseProvider


class FakeProvider(BaseProvider):
    """Minimal in-memory provider so tests never touch a real brokerage."""

    SUPPORTS_FRACTIONAL_SHARES = True

    def __init__(
        self,
        provider: ProviderType,
        holdings: Optional[List[RealPortfolioElement]] = None,
        cash: float = 1000.0,
        fail_with: Optional[Exception] = None,
    ):
        self.PROVIDER = provider
        self._holdings = holdings if holdings is not None else []
        self._cash = Money(value=cash)
        self._fail_with = fail_with
        self.orders: List = []
        self.refresh_count = 0

    # --- surface used by refresh ---
    def clear_cache(self, skip_clearing: Optional[List[str]] = None):
        return None

    def get_holdings(self) -> RealPortfolio:
        if self._fail_with:
            raise self._fail_with
        self.refresh_count += 1
        return RealPortfolio(
            holdings=list(self._holdings), cash=self._cash, provider=self
        )

    def get_profit_or_loss(self) -> ProfitModel:
        return ProfitModel(appreciation=Money(value=1.0), dividends=Money(value=2.0))

    # --- surface used by planning ---
    @property
    def cash(self) -> Money:
        return self._cash

    def get_unsettled_instruments(self) -> Set[str]:
        return set()

    def get_instrument_prices(
        self, tickers, at_day=None
    ) -> Dict[str, Optional[Decimal]]:
        return {ticker: Decimal(10) for ticker in tickers}

    def get_instrument_price(self, ticker, at_day=None):
        return Decimal(10)

    # --- surface used by ordering ---
    def handle_order_element(self, element, dry_run: bool = False):
        if self._fail_with:
            raise self._fail_with
        self.orders.append(element)
        return True

    def get_dividend_details(self, start=None):
        return []


def holding(ticker: str, value: float) -> RealPortfolioElement:
    return RealPortfolioElement(
        ticker=ticker, units=Decimal(1), value=Money(value=value)
    )


@pytest.fixture
def config(test_client: TestClient):
    active = test_client.app.in_app_config  # type: ignore
    active.provider_cache.clear()
    active.holding_cache.clear()
    active.holding_refreshed_at.clear()
    yield active
    active.provider_cache.clear()
    active.holding_cache.clear()
    active.holding_refreshed_at.clear()


def login(config, provider: ProviderType, **kwargs) -> FakeProvider:
    fake = FakeProvider(provider, **kwargs)
    config.provider_cache[provider] = fake
    return fake


def snapshot(provider: ProviderType, ticker: str, value: float, cash: float = 0.0):
    """A client-held snapshot, in the shape the frontend persists it."""
    return {
        "provider": provider.value,
        # deliberately the legacy "USD" spelling, which is what older
        # electron-store data contains
        "cash": {"currency": "USD", "value": cash},
        "holdings": [
            {
                "ticker": ticker,
                "units": 1,
                "value": {"currency": "USD", "value": value},
            }
        ],
        "refreshed_at": 1700000000,
    }


def refresh(test_client: TestClient, **overrides):
    body = {"key": "test", "providers": ["alpaca", "robinhood"]}
    body.update(overrides)
    return test_client.post("/composite_portfolio/refresh", json=body)


def test_refresh_succeeds_with_one_of_two_providers(test_client, config):
    """The headline case: money went into one provider, refresh just that one."""
    login(config, ProviderType.ALPACA, holdings=[holding("AAPL", 100)], cash=500)

    response = refresh(test_client)
    assert response.status_code == 200
    data = response.json()

    assert data["components"]["alpaca"]["status"] == "refreshed"
    assert data["components"]["robinhood"]["status"] == "unauthenticated"
    assert data["partial"] is True
    assert data["degraded_providers"] == ["robinhood"]
    # only the reachable provider's cash counts as spendable
    assert float(data["investable_cash"]["value"]) == 500.0


def test_refresh_merges_client_cache_for_unauthenticated_provider(test_client, config):
    """Holdings we can't re-fetch still contribute to composite totals."""
    login(config, ProviderType.ALPACA, holdings=[holding("AAPL", 100)], cash=500)

    response = refresh(
        test_client, cached=[snapshot(ProviderType.ROBINHOOD, "MSFT", 250, cash=90)]
    )
    assert response.status_code == 200
    data = response.json()

    robinhood = data["components"]["robinhood"]
    assert robinhood["status"] == "unauthenticated"
    assert [h["ticker"] for h in robinhood["holdings"]] == ["MSFT"]
    assert robinhood["refreshed_at"] == 1700000000

    tickers = {h["ticker"] for h in data["holdings"]}
    assert tickers == {"AAPL", "MSFT"}
    # total cash includes the stale provider, investable cash does not
    assert float(data["cash"]["value"]) == 590.0
    assert float(data["investable_cash"]["value"]) == 500.0


def test_refresh_default_targets_only_authenticated_providers(test_client, config):
    """With no explicit target list, we refresh everything we can reach."""
    alpaca = login(config, ProviderType.ALPACA, holdings=[holding("AAPL", 100)])

    refresh(test_client)
    assert alpaca.refresh_count == 1

    # a second call with an explicit narrower target leaves alpaca alone
    refresh(test_client, providers_to_refresh=[])
    assert alpaca.refresh_count == 1
    assert refresh(test_client).json()["components"]["alpaca"]["status"] == "refreshed"
    assert alpaca.refresh_count == 2


def test_refresh_single_provider_serves_others_from_cache(test_client, config):
    alpaca = login(config, ProviderType.ALPACA, holdings=[holding("AAPL", 100)])
    robinhood = login(config, ProviderType.ROBINHOOD, holdings=[holding("MSFT", 50)])
    refresh(test_client)
    assert robinhood.refresh_count == 1

    response = refresh(test_client, providers_to_refresh=["alpaca"])
    data = response.json()
    assert data["components"]["alpaca"]["status"] == "refreshed"
    assert data["components"]["robinhood"]["status"] == "cached"
    assert data["partial"] is False
    assert alpaca.refresh_count == 2
    assert robinhood.refresh_count == 1


def test_skipping_a_provider_preserves_when_it_was_last_refreshed(
    test_client, config
):
    """Refreshing one provider must not make the others look never-fetched.

    Freshness is a timestamp, not a per-call flag: a provider left out of this
    refresh keeps the time of the refresh that did fetch it.
    """
    login(config, ProviderType.ALPACA, holdings=[holding("AAPL", 100)])
    login(config, ProviderType.ROBINHOOD, holdings=[holding("MSFT", 50)])

    both = refresh(test_client).json()["components"]
    robinhood_first_seen = both["robinhood"]["refreshed_at"]
    assert robinhood_first_seen is not None

    after = refresh(test_client, providers_to_refresh=["alpaca"]).json()["components"]
    assert after["robinhood"]["refreshed_at"] == robinhood_first_seen
    assert after["robinhood"]["error"] is None
    assert after["robinhood"]["holdings"], "cached holdings must survive"
    assert after["alpaca"]["refreshed_at"] >= robinhood_first_seen


def test_refresh_isolates_a_failing_provider(test_client, config):
    login(config, ProviderType.ALPACA, holdings=[holding("AAPL", 100)])
    login(config, ProviderType.ROBINHOOD, fail_with=ValueError("provider exploded"))

    data = refresh(test_client).json()
    assert data["components"]["alpaca"]["status"] == "refreshed"
    assert data["components"]["robinhood"]["status"] == "error"
    assert "provider exploded" in data["components"]["robinhood"]["error"]


def test_refresh_drops_login_on_auth_error(test_client, config):
    login(config, ProviderType.ALPACA, holdings=[holding("AAPL", 100)])
    login(config, ProviderType.ROBINHOOD, fail_with=ConfigurationError("token expired"))

    data = refresh(test_client).json()
    assert data["components"]["robinhood"]["status"] == "unauthenticated"
    assert ProviderType.ROBINHOOD not in config.provider_cache


def test_require_all_restores_strict_behaviour(test_client, config):
    login(config, ProviderType.ALPACA, holdings=[holding("AAPL", 100)])

    response = refresh(test_client, require_all=True)
    assert response.status_code == 401
    assert "robinhood" in response.json()["detail"]


def test_require_all_surfaces_a_refresh_failure(test_client, config):
    """Strict mode reports provider errors, not just missing logins."""
    login(config, ProviderType.ALPACA, holdings=[holding("AAPL", 100)])
    login(config, ProviderType.ROBINHOOD, fail_with=ValueError("provider exploded"))

    response = refresh(test_client, require_all=True)
    assert response.status_code == 422
    assert "provider exploded" in response.json()["detail"]


def test_live_data_wins_over_a_client_snapshot(test_client, config):
    """A stale client copy must never overwrite what we just fetched."""
    login(config, ProviderType.ALPACA, holdings=[holding("AAPL", 100)], cash=500)

    data = refresh(
        test_client,
        # the client's saved copy of alpaca disagrees with reality
        cached=[snapshot(ProviderType.ALPACA, "STALE", 999, cash=1)],
    ).json()

    alpaca = data["components"]["alpaca"]
    assert [h["ticker"] for h in alpaca["holdings"]] == ["AAPL"]
    assert float(alpaca["cash"]["value"]) == 500.0


def test_snapshot_tolerates_unrecognised_currency(test_client, config):
    """Saved data written by older versions must not fail validation."""
    login(config, ProviderType.ALPACA, holdings=[], cash=0)
    payload = snapshot(ProviderType.ROBINHOOD, "MSFT", 250, cash=90)
    payload["cash"]["currency"] = "XYZ"
    payload["holdings"][0]["value"] = {"value": 250}

    response = refresh(test_client, cached=[payload])
    assert response.status_code == 200
    robinhood = response.json()["components"]["robinhood"]
    assert float(robinhood["holdings"][0]["value"]["value"]) == 250.0
    assert float(robinhood["cash"]["value"]) == 90.0


def test_provider_status_endpoint(test_client, config):
    login(config, ProviderType.ALPACA, holdings=[holding("AAPL", 100)])
    refresh(test_client)

    statuses = {
        row["provider"]: row for row in test_client.get("/provider_status").json()["providers"]
    }
    assert statuses["alpaca"]["authenticated"] is True
    assert statuses["alpaca"]["has_cached_holdings"] is True
    assert statuses["alpaca"]["refreshed_at"] is not None
    assert statuses["robinhood"]["authenticated"] is False


def plan(test_client: TestClient, **overrides):
    body = {
        "index": "total_market",
        "providers": ["alpaca", "robinhood"],
        "to_purchase": 100,
        "target_size": 10000,
    }
    body.update(overrides)
    return test_client.post("/plan_composite_purchase", json=body)


def test_plan_routes_orders_only_to_authenticated_providers(test_client, config):
    login(config, ProviderType.ALPACA, holdings=[holding("AAPL", 100)], cash=500)

    response = plan(
        test_client, cached=[snapshot(ProviderType.ROBINHOOD, "MSFT", 250, cash=900)]
    )
    assert response.status_code == 200
    data = response.json()

    assert data["order_providers"] == ["alpaca"]
    assert data["skipped_providers"] == ["robinhood"]
    assert data["to_buy"], "expected a non-empty plan"
    # no order may be routed to a provider we cannot reach
    assert {order["provider"] for order in data["to_buy"]} == {"alpaca"}


def test_plan_counts_cached_holdings_toward_target(test_client, config):
    """A stale provider's holdings reduce what we still need to buy."""
    login(config, ProviderType.ALPACA, holdings=[], cash=500)

    baseline = plan(test_client).json()["to_buy"]
    assert baseline, "expected a non-empty baseline plan"

    def value_of(orders, ticker):
        return sum(
            float(o["value"]["value"]) for o in orders if o["ticker"] == ticker
        )

    # already owning a large position in the most-wanted ticker, at a provider
    # we cannot reach, should take it off the shopping list
    top_ticker = max(baseline, key=lambda o: float(o["value"]["value"]))["ticker"]
    config.holding_cache.clear()

    with_cache = plan(
        test_client,
        cached=[snapshot(ProviderType.ROBINHOOD, top_ticker, 9000)],
    ).json()["to_buy"]

    assert value_of(with_cache, top_ticker) < value_of(baseline, top_ticker)


def test_plan_requires_at_least_one_authenticated_provider(test_client, config):
    response = plan(test_client)
    assert response.status_code == 401
    assert "at least one provider" in response.json()["detail"]


def test_plan_require_all_rejects_partial(test_client, config):
    login(config, ProviderType.ALPACA, holdings=[holding("AAPL", 100)], cash=500)
    response = plan(test_client, require_all=True)
    assert response.status_code == 401


def test_plan_reprices_against_a_reachable_provider(test_client, config):
    """Reweighting needs live prices, so an unreachable pricing provider is
    swapped for one we can actually query."""
    login(config, ProviderType.ALPACA, holdings=[], cash=500)

    response = plan(
        test_client,
        provider="robinhood",
        reweight=True,
        cached=[snapshot(ProviderType.ROBINHOOD, "MSFT", 250, cash=900)],
    )
    assert response.status_code == 200
    assert response.json()["order_providers"] == ["alpaca"]


def test_plan_require_all_reraises_an_expired_login(test_client, config):
    login(config, ProviderType.ALPACA, holdings=[], cash=500)
    login(config, ProviderType.ROBINHOOD, fail_with=ConfigurationError("expired"))

    response = plan(test_client, require_all=True)
    assert response.status_code == 401
    assert "expired" in response.json()["detail"]


def test_plan_survives_a_login_expiring_mid_plan(test_client, config):
    """A provider whose credentials fail while planning degrades to its cache."""
    login(config, ProviderType.ALPACA, holdings=[], cash=500)
    login(config, ProviderType.ROBINHOOD, fail_with=ConfigurationError("expired"))

    response = plan(
        test_client, cached=[snapshot(ProviderType.ROBINHOOD, "MSFT", 250, cash=900)]
    )
    assert response.status_code == 200
    data = response.json()
    assert data["skipped_providers"] == ["robinhood"]
    assert data["order_providers"] == ["alpaca"]
    # the failed login was forgotten, its holdings were not
    assert ProviderType.ROBINHOOD not in config.provider_cache
    assert config.holding_cache[ProviderType.ROBINHOOD].holdings


def test_orders_place_on_reachable_providers_and_fail_the_rest(test_client, config):
    alpaca = login(config, ProviderType.ALPACA, holdings=[], cash=500)

    response = test_client.post(
        "/buy_index_from_plan_multi_provider",
        json={
            "providers": ["alpaca", "robinhood"],
            "plan": {
                "to_buy": [
                    {
                        "ticker": "AAPL",
                        "order_type": "BUY",
                        "value": {"currency": "$", "value": 10},
                        "qty": None,
                        "provider": "alpaca",
                        "status": "requested",
                        "message": None,
                    },
                    {
                        "ticker": "MSFT",
                        "order_type": "BUY",
                        "value": {"currency": "$", "value": 10},
                        "qty": None,
                        "provider": "robinhood",
                        "status": "requested",
                        "message": None,
                    },
                ]
            },
        },
    )
    assert response.status_code == 200
    data = response.json()
    by_ticker = {order["ticker"]: order for order in data["orders"]}

    assert by_ticker["AAPL"]["status"] == "placed"
    assert by_ticker["MSFT"]["status"] == "failed"
    assert "Not authenticated to robinhood" in by_ticker["MSFT"]["message"]
    assert data["skipped_providers"] == ["robinhood"]
    assert [order.ticker for order in alpaca.orders] == ["AAPL"]


def test_expired_login_never_receives_orders(test_client, config):
    """A cached portfolio outlives the login that produced it.

    After a successful refresh the cache holds a RealPortfolio still pointing
    at a live provider object. If that login later drops, the snapshot must be
    detached before planning - otherwise the planner treats the dead provider
    as an order destination.
    """
    login(config, ProviderType.ALPACA, holdings=[], cash=500)
    login(config, ProviderType.ROBINHOOD, holdings=[holding("MSFT", 250)], cash=900)
    refresh(test_client)
    assert config.holding_cache[ProviderType.ROBINHOOD].provider is not None

    # the login expires; holdings we already fetched stay behind
    config.drop_login(ProviderType.ROBINHOOD)

    response = plan(test_client)
    assert response.status_code == 200
    data = response.json()
    assert data["skipped_providers"] == ["robinhood"]
    assert {order["provider"] for order in data["to_buy"]} == {"alpaca"}
    # the stale holdings still counted toward the target
    assert any(h for h in data["to_buy"]), "expected a plan"
    assert config.holding_cache[ProviderType.ROBINHOOD].holdings


def test_end_to_end_single_provider_story(test_client, config):
    """Money went into alpaca. Log into alpaca only, refresh, buy - done.

    Robinhood is never authenticated; its holdings come entirely from the
    client's saved copy and it receives no orders.
    """
    alpaca = login(config, ProviderType.ALPACA, holdings=[], cash=500)
    saved = [snapshot(ProviderType.ROBINHOOD, "MSFT", 250, cash=90)]

    refreshed = refresh(test_client, cached=saved).json()
    assert refreshed["components"]["alpaca"]["status"] == "refreshed"
    assert refreshed["components"]["robinhood"]["status"] == "unauthenticated"
    assert float(refreshed["investable_cash"]["value"]) == 500.0

    planned = plan(test_client, cached=saved).json()
    assert planned["skipped_providers"] == ["robinhood"]
    assert {order["provider"] for order in planned["to_buy"]} == {"alpaca"}

    placed = test_client.post(
        "/buy_index_from_plan_multi_provider",
        json={"providers": ["alpaca", "robinhood"], "plan": planned},
    ).json()
    assert placed["skipped_providers"] == []
    assert {order["status"] for order in placed["orders"]} == {"placed"}
    assert len(alpaca.orders) == len(planned["to_buy"])


def order_payload(provider: str, ticker: str):
    return {
        "ticker": ticker,
        "order_type": "BUY",
        "value": {"currency": "$", "value": 10},
        "qty": None,
        "provider": provider,
        "status": "requested",
        "message": None,
    }


def test_orders_require_all_rejects_partial(test_client, config):
    login(config, ProviderType.ALPACA, holdings=[], cash=500)

    response = test_client.post(
        "/buy_index_from_plan_multi_provider",
        json={
            "providers": ["alpaca", "robinhood"],
            "require_all": True,
            "plan": {
                "to_buy": [
                    order_payload("alpaca", "AAPL"),
                    order_payload("robinhood", "MSFT"),
                ]
            },
        },
    )
    assert response.status_code == 401
    assert "robinhood" in response.json()["detail"]


def test_order_auth_failure_drops_the_login(test_client, config):
    """Credentials that fail mid-order are forgotten so the UI can prompt."""
    login(config, ProviderType.ALPACA, fail_with=ConfigurationError("expired"))

    response = test_client.post(
        "/buy_index_from_plan_multi_provider",
        json={
            "providers": ["alpaca"],
            "plan": {"to_buy": [order_payload("alpaca", "AAPL")]},
        },
    )
    assert response.status_code == 200
    assert response.json()["orders"][0]["status"] == "failed"
    assert ProviderType.ALPACA not in config.provider_cache


def test_order_auth_failure_short_circuits_that_providers_remaining_orders(
    test_client, config
):
    """One expired login should not be retried once per remaining order."""
    alpaca = login(config, ProviderType.ALPACA, fail_with=ConfigurationError("expired"))

    response = test_client.post(
        "/buy_index_from_plan_multi_provider",
        json={
            "providers": ["alpaca"],
            "plan": {
                "to_buy": [
                    order_payload("alpaca", "AAPL"),
                    order_payload("alpaca", "MSFT"),
                ]
            },
        },
    )
    assert response.status_code == 200
    orders = {order["ticker"]: order for order in response.json()["orders"]}
    assert orders["AAPL"]["message"] == "expired"
    assert "earlier order" in orders["MSFT"]["message"]
    assert alpaca.orders == []


def test_order_rejection_does_not_drop_the_login(test_client, config):
    """A rejected order is a trading problem, not an auth problem."""
    login(config, ProviderType.ALPACA, fail_with=OrderError("insufficient buying power"))

    response = test_client.post(
        "/buy_index_from_plan_multi_provider",
        json={
            "providers": ["alpaca"],
            "plan": {"to_buy": [order_payload("alpaca", "AAPL")]},
        },
    )
    order = response.json()["orders"][0]
    assert order["status"] == "failed"
    assert order["message"] == "insufficient buying power"
    # still logged in, so the user can adjust and retry
    assert ProviderType.ALPACA in config.provider_cache


def test_orders_reject_when_no_provider_is_reachable(test_client, config):
    response = test_client.post(
        "/buy_index_from_plan_multi_provider",
        json={
            "providers": ["robinhood"],
            "plan": {
                "to_buy": [
                    {
                        "ticker": "MSFT",
                        "order_type": "BUY",
                        "value": {"currency": "$", "value": 10},
                        "qty": None,
                        "provider": "robinhood",
                        "status": "requested",
                        "message": None,
                    }
                ]
            },
        },
    )
    assert response.status_code == 401
