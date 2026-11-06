"""Uploaded orders: the only path that can sell, so it's held to what's owned."""

from decimal import Decimal

import pytest
from py_portfolio_index.enums import ProviderType
from py_portfolio_index.models import Money, RealPortfolioElement
from test_partial_auth import config, holding, login, order_payload  # noqa: F401


def position(ticker: str, units, value, gain=0) -> RealPortfolioElement:
    return RealPortfolioElement(
        ticker=ticker,
        units=Decimal(str(units)),
        value=Money(value=value),
        appreciation=Money(value=gain),
    )


def plan(client, orders, providers=("alpaca", "robinhood")):
    response = client.post(
        "/plan_uploaded_orders",
        json={"orders": orders, "providers": list(providers)},
    )
    assert response.status_code == 200, response.text
    return response.json()


def place(client, planned, providers=("alpaca", "robinhood"), allow_sells=True):
    response = client.post(
        "/buy_index_from_plan_multi_provider",
        json={"plan": planned, "providers": list(providers), "allow_sells": allow_sells},
    )
    assert response.status_code == 200, response.text
    return response.json()["orders"]


def cache(config, provider, fake):  # noqa: F811
    config.holding_cache[provider] = fake.get_holdings()


def seller(config, provider, holdings, fractional=True):  # noqa: F811
    fake = login(config, provider, holdings=holdings, cash=0)
    fake.SUPPORTS_FRACTIONAL_SHARES = fractional
    cache(config, provider, fake)
    return fake


def test_sell_with_a_broker_stays_there(test_client, config):  # noqa: F811
    seller(config, ProviderType.ALPACA, [position("MC", 10, 500, -50)])
    seller(config, ProviderType.ROBINHOOD, [position("MC", 10, 500, -400)])

    result = plan(test_client, [{"ticker": "MC", "side": "SELL", "shares": 4, "broker": "alpaca"}])

    assert [(x["provider"], x["qty"]) for x in result["to_buy"]] == [("alpaca", 4)]
    assert float(result["to_buy"][0]["estimated_gain"]["value"]) == pytest.approx(-20)
    assert result["rejected"] == []


def test_sell_without_a_broker_takes_the_biggest_loss_first(test_client, config):  # noqa: F811
    seller(config, ProviderType.ALPACA, [position("MC", 10, 500, 100)])
    seller(config, ProviderType.ROBINHOOD, [position("MC", 10, 500, -200)])

    result = plan(test_client, [{"ticker": "MC", "side": "SELL", "shares": 15}])

    assert [(x["provider"], x["qty"]) for x in result["to_buy"]] == [
        ("robinhood", 10),
        ("alpaca", 5),
    ]


def test_sell_leaves_a_position_with_no_basis_for_last(test_client, config):  # noqa: F811
    seller(config, ProviderType.ALPACA, [position("MC", 10, 500, 0)])
    seller(config, ProviderType.ROBINHOOD, [position("MC", 10, 500, 400)])

    result = plan(test_client, [{"ticker": "MC", "side": "SELL", "shares": 12}])

    assert [x["provider"] for x in result["to_buy"]] == ["robinhood", "alpaca"]


def test_sell_by_value_converts_to_shares(test_client, config):  # noqa: F811
    seller(config, ProviderType.ALPACA, [position("MC", 10, 500)])

    result = plan(test_client, [{"ticker": "MC", "side": "SELL", "value": 100}], ["alpaca"])

    assert [x["qty"] for x in result["to_buy"]] == [2]


def test_sell_is_capped_at_shares_held_and_says_so(test_client, config):  # noqa: F811
    seller(config, ProviderType.ALPACA, [position("MC", 3, 150)])

    result = plan(test_client, [{"ticker": "MC", "side": "SELL", "shares": 5}], ["alpaca"])

    assert [x["qty"] for x in result["to_buy"]] == [3]
    assert "2 shares" in result["rejected"][0]["reason"]


def test_repeated_rows_cannot_sell_the_same_shares_twice(test_client, config):  # noqa: F811
    seller(config, ProviderType.ALPACA, [position("MC", 3, 150)])
    row = {"ticker": "MC", "side": "SELL", "shares": 3}

    result = plan(test_client, [row, row], ["alpaca"])

    assert [x["qty"] for x in result["to_buy"]] == [3]
    assert len(result["rejected"]) == 1


def test_whole_share_brokers_get_whole_shares(test_client, config):  # noqa: F811
    seller(config, ProviderType.ALPACA, [position("MC", "2.5", 125)], fractional=False)

    result = plan(test_client, [{"ticker": "MC", "side": "SELL", "shares": 2.5}], ["alpaca"])

    assert [x["qty"] for x in result["to_buy"]] == [2]


def test_sell_of_something_not_held_is_rejected(test_client, config):  # noqa: F811
    seller(config, ProviderType.ALPACA, [])

    result = plan(test_client, [{"ticker": "MC", "side": "SELL", "shares": 1}], ["alpaca"])

    assert result["to_buy"] == []
    assert "No shares of MC" in result["rejected"][0]["reason"]


def test_sell_at_a_provider_we_are_not_logged_into_is_rejected(test_client, config):  # noqa: F811
    fake = seller(config, ProviderType.ALPACA, [position("MC", 3, 150)])
    config.provider_cache.pop(fake.PROVIDER)

    result = plan(test_client, [{"ticker": "MC", "side": "SELL", "shares": 1, "broker": "alpaca"}])

    assert result["to_buy"] == []


def test_a_buy_needs_a_broker(test_client, config):  # noqa: F811
    seller(config, ProviderType.ALPACA, [])

    result = plan(test_client, [{"ticker": "RHHBY", "side": "BUY", "shares": 1}], ["alpaca"])

    assert result["to_buy"] == []
    assert result["rejected"][0]["reason"] == "A buy needs a broker."


def test_uploaded_sell_places_after_opting_in(test_client, config):  # noqa: F811
    fake = seller(config, ProviderType.ALPACA, [position("MC", 3, 150)])
    planned = plan(test_client, [{"ticker": "MC", "side": "SELL", "shares": 3}], ["alpaca"])

    orders = place(test_client, planned, ["alpaca"])

    assert [x["status"] for x in orders] == ["placed"]
    assert [(x.ticker, x.qty, x.order_type.value) for x in fake.orders] == [("MC", 3, "SELL")]


def test_uploaded_plan_still_needs_the_opt_in(test_client, config):  # noqa: F811
    fake = seller(config, ProviderType.ALPACA, [position("MC", 3, 150)])
    planned = plan(test_client, [{"ticker": "MC", "side": "SELL", "shares": 3}], ["alpaca"])

    orders = place(test_client, planned, ["alpaca"], allow_sells=False)

    assert [x["status"] for x in orders] == ["failed"]
    assert fake.orders == []


def test_submitting_twice_cannot_sell_twice(test_client, config):  # noqa: F811
    fake = seller(config, ProviderType.ALPACA, [position("MC", 3, 150)])
    planned = plan(test_client, [{"ticker": "MC", "side": "SELL", "shares": 3}], ["alpaca"])

    place(test_client, planned, ["alpaca"])
    second = place(test_client, planned, ["alpaca"])

    assert [x["status"] for x in second] == ["failed"]
    assert len(fake.orders) == 1


def test_placement_refuses_more_than_held_whatever_the_plan_says(test_client, config):  # noqa: F811
    fake = seller(config, ProviderType.ALPACA, [position("MC", 3, 150)])
    order = {**order_payload("alpaca", "MC"), "order_type": "SELL", "qty": 4, "value": None}

    orders = place(test_client, {"to_buy": [order]}, ["alpaca"])

    assert [x["status"] for x in orders] == ["failed"]
    assert fake.orders == []
