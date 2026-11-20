"""The ticker tooltip: details from the default provider, a price from the best
quoter logged in."""

from decimal import Decimal

from fastapi.testclient import TestClient
from py_portfolio_index.enums import ProviderType
from py_portfolio_index.exceptions import PriceFetchError
from test_partial_auth import FakeProvider, config, login  # noqa: F401


class Quoter(FakeProvider):
    def __init__(self, provider: ProviderType, priority: int, prices: dict[str, Decimal]):
        super().__init__(provider)
        self.QUOTE_PRIORITY = priority
        self.prices = prices
        self.asked: list[str] = []

    def get_instrument_price(self, ticker, at_day=None):
        self.asked.append(ticker)
        if ticker not in self.prices:
            raise PriceFetchError([ticker], f"No price for {ticker}")
        return self.prices[ticker]


def test_price_comes_from_the_best_quoter(test_client: TestClient, config):  # noqa: F811
    low = Quoter(ProviderType.ALPACA, 1, {"AAPL": Decimal(1)})
    high = Quoter(ProviderType.SCHWAB, 4, {"AAPL": Decimal("200.5")})
    config.provider_cache[ProviderType.ALPACA] = low
    config.provider_cache[ProviderType.SCHWAB] = high

    body = test_client.get("/stock_info/AAPL").json()

    assert body["ticker"] == "AAPL"
    assert body["name"]
    assert (body["price"], body["price_provider"]) == (200.5, "schwab")
    assert low.asked == []


def test_quoter_that_cannot_price_hands_off(test_client: TestClient, config):  # noqa: F811
    config.provider_cache[ProviderType.SCHWAB] = Quoter(ProviderType.SCHWAB, 4, {})
    config.provider_cache[ProviderType.ROBINHOOD] = Quoter(
        ProviderType.ROBINHOOD, 3, {"TCEHY": Decimal("70.25")}
    )

    body = test_client.get("/stock_info/TCEHY").json()

    assert (body["price"], body["price_provider"]) == (70.25, "robinhood")


def test_details_without_a_price(test_client: TestClient, config):  # noqa: F811
    # FakeProvider has no instrument lookup, so the bundled details are used
    config.provider_cache[ProviderType.ALPACA] = Quoter(ProviderType.ALPACA, 1, {})

    body = test_client.get("/stock_info/AAPL").json()

    assert body["ticker"] == "AAPL"
    assert body["exchange"]
    assert body["price"] is None
    assert body["price_provider"] is None


def test_unknown_ticker_still_answers(test_client: TestClient, config):  # noqa: F811
    login(config, ProviderType.ALPACA)

    body = test_client.get("/stock_info/NOTAREALTICKERX").json()

    assert body["ticker"] == "NOTAREALTICKERX"
    assert body["price"] == 10.0


def test_no_provider_is_unauthorized(test_client: TestClient, config):  # noqa: F811
    assert test_client.get("/stock_info/AAPL").status_code == 401
