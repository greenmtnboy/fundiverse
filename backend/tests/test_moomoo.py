from main import refresh_sub_portfolio, login, LoginRequest

from py_portfolio_index.enums import ProviderType

def test_moomoo():
    login(LoginRequest(
        key='abc',
        secret = '123',
        provider = ProviderType.MOOMOO
    ))
    x = refresh_sub_portfolio(ProviderType.MOOMOO, providers_to_refresh=[ProviderType.MOOMOO])
    print(x)
