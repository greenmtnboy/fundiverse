"""A provider that borrows quotes (Moomoo) must still place orders when that
quote source can't price the ticker or has been replaced by a newer login."""

from decimal import Decimal

import pytest
from py_portfolio_index.enums import ProviderType
from py_portfolio_index.exceptions import ConfigurationError, PriceFetchError
from py_portfolio_index.portfolio_providers.base_portfolio import BaseProvider
from test_order_upload import place, position
from test_partial_auth import FakeProvider, config  # noqa: F401


class Quoter(FakeProvider):
    def __init__(self, provider, price=None, fail_with=None):
        super().__init__(provider)
        self._price = price
        self._quote_error = fail_with

    def get_instrument_price(self, ticker, at_day=None):
        if self._quote_error:
            raise self._quote_error
        return self._price


class Borrower(FakeProvider):
    """Places orders through the real BaseProvider path, quoting elsewhere."""

    handle_order_element = BaseProvider.handle_order_element
    get_instrument_price = BaseProvider.get_instrument_price
    SUPPORTS_LIMIT_ORDERS = True

    def __init__(self, provider, quote_provider, **kwargs):
        super().__init__(provider, **kwargs)
        self._quote_provider = quote_provider
        self.sold: list = []

    def sell_instrument(self, ticker, qty, value=None, limit_price=None):
        self.sold.append((ticker, qty, value))
        return True


def sell_order(price=None):
    order = {
        "ticker": "TCEHY",
        "order_type": "SELL",
        "qty": 3,
        "value": None,
        "provider": "moomoo",
        "status": None,
        "message": None,
    }
    if price:
        order["price"] = {"currency": "$", "value": price}
    return order


def test_sell_falls_back_to_the_planned_price(test_client, config):  # noqa: F811
    dead = Quoter(
        ProviderType.SCHWAB, fail_with=PriceFetchError(["TCEHY"], ConfigurationError("expired"))
    )
    moomoo = Borrower(ProviderType.MOOMOO, dead, holdings=[position("TCEHY", 10, 430)])
    config.provider_cache[ProviderType.MOOMOO] = moomoo
    config.holding_cache[ProviderType.MOOMOO] = moomoo.get_holdings()

    orders = place(
        test_client,
        {"to_buy": [sell_order(price=43.7)]},
        providers=("moomoo",),
    )

    assert orders[0]["status"] == "placed", orders[0]["message"]
    assert float(moomoo.sold[0][2].decimal) == pytest.approx(3 * 43.7)


def test_relogin_of_the_quote_provider_reaches_moomoo(test_client, config, monkeypatch):  # noqa: F811
    import main

    old = Quoter(
        ProviderType.SCHWAB, fail_with=PriceFetchError(["TCEHY"], ConfigurationError("expired"))
    )
    moomoo = Borrower(ProviderType.MOOMOO, old, holdings=[position("TCEHY", 10, 430)])
    config.provider_cache[ProviderType.MOOMOO] = moomoo
    config.holding_cache[ProviderType.MOOMOO] = moomoo.get_holdings()
    # schwab's token expired and the user signed in to it again
    fresh = Quoter(ProviderType.SCHWAB, price=Decimal("43.7"))
    monkeypatch.setitem(main.PROVIDER_LOGINS, ProviderType.SCHWAB, lambda _: fresh)
    main.login(main.LoginRequest(key="k", secret="s", provider=ProviderType.SCHWAB))

    orders = place(test_client, {"to_buy": [sell_order()]}, providers=("moomoo",))

    assert orders[0]["status"] == "placed", orders[0]["message"]


def test_changing_the_quote_provider_takes_effect_without_signing_in_again(
    test_client,
    config,  # noqa: F811
):
    alpaca = Quoter(ProviderType.ALPACA, fail_with=PriceFetchError(["TCEHY"], "not in feed"))
    schwab = Quoter(ProviderType.SCHWAB, price=Decimal("43.7"))
    moomoo = Borrower(ProviderType.MOOMOO, alpaca, holdings=[position("TCEHY", 10, 430)])
    config.provider_cache[ProviderType.ALPACA] = alpaca
    config.provider_cache[ProviderType.SCHWAB] = schwab
    config.provider_cache[ProviderType.MOOMOO] = moomoo
    config.holding_cache[ProviderType.MOOMOO] = moomoo.get_holdings()

    response = test_client.post(
        "/login",
        json={"key": "k", "secret": "s", "provider": "moomoo", "quote_provider": "schwab"},
    )

    assert response.status_code == 200, response.text
    assert config.provider_cache[ProviderType.MOOMOO] is moomoo
    orders = place(test_client, {"to_buy": [sell_order()]}, providers=("moomoo",))
    assert orders[0]["status"] == "placed", orders[0]["message"]


def test_changing_to_a_quote_provider_that_is_not_signed_in_is_refused(
    test_client,
    config,  # noqa: F811
):
    alpaca = Quoter(ProviderType.ALPACA, price=Decimal("43.7"))
    moomoo = Borrower(ProviderType.MOOMOO, alpaca)
    config.provider_cache[ProviderType.ALPACA] = alpaca
    config.provider_cache[ProviderType.MOOMOO] = moomoo

    response = test_client.post(
        "/login",
        json={"key": "k", "secret": "s", "provider": "moomoo", "quote_provider": "schwab"},
    )

    assert response.status_code == 400
    assert moomoo._quote_provider is alpaca
