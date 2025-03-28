from py_portfolio_index.enums import ProviderType

from main import LoginRequest, login, refresh_sub_portfolio


def test_moomoo():
    login(LoginRequest(key="abc", secret="123", provider=ProviderType.ALPACA))
    login(LoginRequest(key="abc", secret="123", provider=ProviderType.MOOMOO, quote_provider=ProviderType.ALPACA))
    x = refresh_sub_portfolio(
        ProviderType.MOOMOO, providers_to_refresh=[ProviderType.MOOMOO]
    )
    print(x)
