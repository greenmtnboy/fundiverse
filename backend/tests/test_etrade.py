from typing import Any

import pytest
from fastapi.testclient import TestClient
from py_portfolio_index.enums import ProviderType
from py_portfolio_index.portfolio_providers.helpers.etrade import ETradeAuthContext

import main

AUTH_URL = "https://us.etrade.com/e/t/etws/authorize?key=key&token=req-token"


def _context(sandbox: bool = True) -> ETradeAuthContext:
    return ETradeAuthContext(
        authorization_url=AUTH_URL,
        api_key="key",
        api_secret="secret",
        sandbox=sandbox,
        flow=object(),
    )


class DummyETradeProvider:
    API_KEY_ENV = "ETRADE_API_KEY"
    API_SECRET_ENV = "ETRADE_API_SECRET"
    SANDBOX_ENV = "ETRADE_SANDBOX"
    PROVIDER = ProviderType.ETRADE

    def __init__(self, external_auth: bool = False, sandbox: bool = False):
        self.external_auth = external_auth
        self.sandbox = sandbox


@pytest.fixture
def etrade_env(monkeypatch, test_client: TestClient):
    """Fake out the library's auth seams and reset login state."""
    state: dict[str, Any] = {
        "cached_token": None,
        "completed": [],
        "context": _context(),
    }

    def fake_create_login_context(api_key, api_secret, sandbox=False, callback_url="oob"):
        if state["cached_token"]:
            return None
        return state["context"]

    def fake_complete_authorization(context, verifier):
        state["completed"].append((context, verifier))
        state["cached_token"] = {"oauth_token": "tok", "oauth_token_secret": "s"}

    monkeypatch.setattr(main, "etrade_create_login_context", fake_create_login_context)
    monkeypatch.setattr(main, "etrade_complete_authorization", fake_complete_authorization)
    monkeypatch.setattr(main, "etrade_load_cached_token", lambda sandbox=False: state["cached_token"])
    monkeypatch.setattr(main, "ETradeProvider", DummyETradeProvider)

    main.IN_APP_CONFIG.provider_cache.pop(ProviderType.ETRADE, None)
    main.IN_APP_CONFIG.pending_etrade_response = None
    yield state
    main.IN_APP_CONFIG.provider_cache.pop(ProviderType.ETRADE, None)
    main.IN_APP_CONFIG.pending_etrade_response = None


LOGIN_BODY = {
    "key": "key",
    "secret": "secret",
    "provider": "etrade",
    "sandbox": "true",
}


def test_login_starts_authorization_flow(etrade_env, test_client: TestClient):
    response = test_client.post("/login", json=LOGIN_BODY)
    assert response.status_code == 303
    assert response.json()["detail"] == AUTH_URL
    assert main.IN_APP_CONFIG.pending_etrade_response is etrade_env["context"]


def test_login_completes_with_pasted_verifier(etrade_env, test_client: TestClient):
    test_client.post("/login", json=LOGIN_BODY)

    response = test_client.post("/login", json={**LOGIN_BODY, "extra_factor": "code123"})
    assert response.status_code == 200
    assert etrade_env["completed"] == [(etrade_env["context"], "code123")]
    provider = main.IN_APP_CONFIG.provider_cache[ProviderType.ETRADE]
    assert isinstance(provider, DummyETradeProvider)
    assert provider.external_auth
    assert provider.sandbox


def test_resubmit_without_verifier_reissues_url(etrade_env, test_client: TestClient):
    test_client.post("/login", json=LOGIN_BODY)

    # no code pasted and the callback has not fired: same URL comes back
    response = test_client.post("/login", json={**LOGIN_BODY, "wait_for_external_auth": True})
    assert response.status_code == 303
    assert response.json()["detail"] == AUTH_URL
    assert not etrade_env["completed"]


def test_callback_endpoint_completes_pending_flow(etrade_env, test_client: TestClient):
    test_client.post("/login", json=LOGIN_BODY)

    # E*TRADE redirects the user's browser here once a callback URL is registered;
    # the route must work without a bearer token
    main.IN_APP_CONFIG.validate = True
    try:
        response = test_client.get("/public/etrade/callback", params={"oauth_verifier": "cb-code", "oauth_token": "req-token"})
    finally:
        main.IN_APP_CONFIG.validate = False
    assert response.status_code == 200
    assert "authorization complete" in response.text.lower()
    assert etrade_env["completed"] == [(etrade_env["context"], "cb-code")]
    assert main.IN_APP_CONFIG.pending_etrade_response is None

    # the follow-up login finds the cached token and constructs the provider
    response = test_client.post("/login", json={**LOGIN_BODY, "wait_for_external_auth": True})
    assert response.status_code == 200
    assert ProviderType.ETRADE in main.IN_APP_CONFIG.provider_cache


def test_callback_without_pending_flow_404s(etrade_env, test_client: TestClient):
    response = test_client.get("/public/etrade/callback", params={"oauth_verifier": "cb-code"})
    assert response.status_code == 404


def test_callback_without_verifier_400s(etrade_env, test_client: TestClient):
    test_client.post("/login", json=LOGIN_BODY)
    response = test_client.get("/public/etrade/callback")
    assert response.status_code == 400
    assert main.IN_APP_CONFIG.pending_etrade_response is not None


def test_login_with_valid_cached_token_skips_flow(etrade_env, test_client: TestClient):
    etrade_env["cached_token"] = {"oauth_token": "tok", "oauth_token_secret": "s"}
    response = test_client.post("/login", json=LOGIN_BODY)
    assert response.status_code == 200
    assert ProviderType.ETRADE in main.IN_APP_CONFIG.provider_cache


def test_sandbox_flag_parsing():
    assert main.LoginRequest(key="k", secret="s", provider=ProviderType.ETRADE, sandbox="true").sandbox_enabled
    assert main.LoginRequest(key="k", secret="s", provider=ProviderType.ETRADE, sandbox=True).sandbox_enabled
    assert not main.LoginRequest(key="k", secret="s", provider=ProviderType.ETRADE, sandbox="").sandbox_enabled
    assert not main.LoginRequest(key="k", secret="s", provider=ProviderType.ETRADE).sandbox_enabled
