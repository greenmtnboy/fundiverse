"""Coverage for the schwab external-login handshake.

Schwab's flow spans two requests: the first hands back an authorization URL and
leaves a subprocess listening on the callback port, the second redeems the code
that subprocess captured. The pair only works if both requests operate on the
*same* auth context - a second context would listen on a queue that the already
bound callback port never feeds, so its redemption blocks until callback_timeout.
"""

import multiprocessing
from pathlib import Path
from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient
from py_portfolio_index.enums import ProviderType
from py_portfolio_index.portfolio_providers.helpers.schwab import SchwabAuthContext

import main

AUTH_URL = "https://api.schwabapi.com/v1/oauth/authorize?client_id=key&state=abc"


def _context(pid: int = 4242) -> SchwabAuthContext:
    return SchwabAuthContext(
        authorization_url=AUTH_URL,
        api_key="key",
        app_secret="secret",
        callback_url="https://127.0.0.1:8182",
        token_path=Path("schwab_token.json"),
        callback_timeout=300.0,
        output_queue=multiprocessing.Queue(),
        oauth=object(),
        server_pid=pid,
    )


class DummySchwabProvider:
    API_KEY_ENV = "SCHWAB_API_KEY"
    APP_SECRET_ENV = "SCHWAB_APP_SECRET"
    PROVIDER = ProviderType.SCHWAB

    def __init__(self, external_auth: bool = False):
        self.external_auth = external_auth


@pytest.fixture
def schwab_env(monkeypatch, test_client: TestClient):
    """Fake out the library's auth seams and reset login state."""
    state: Dict[str, Any] = {
        "contexts": [],
        "fetched": [],
        "discarded": [],
        "token_valid": False,
        "live": True,
    }

    def fake_create_login_context(api_key, app_secret):
        if state["token_valid"]:
            return None
        context = _context(pid=4242 + len(state["contexts"]))
        state["contexts"].append(context)
        return context

    def fake_fetch_response(context):
        state["fetched"].append(context)
        state["token_valid"] = True

    monkeypatch.setattr(main, "create_login_context", fake_create_login_context)
    monkeypatch.setattr(main, "fetch_response", fake_fetch_response)
    monkeypatch.setattr(main, "SchwabProvider", DummySchwabProvider)
    monkeypatch.setattr(main, "schwab_context_is_live", lambda ctx: state["live"])
    monkeypatch.setattr(
        main, "discard_schwab_context", lambda ctx: state["discarded"].append(ctx)
    )

    main.IN_APP_CONFIG.provider_cache.pop(ProviderType.SCHWAB, None)
    main.IN_APP_CONFIG.pending_schwab_response = None
    yield state
    main.IN_APP_CONFIG.provider_cache.pop(ProviderType.SCHWAB, None)
    main.IN_APP_CONFIG.pending_schwab_response = None


LOGIN_BODY = {"key": "key", "secret": "secret", "provider": "schwab"}


def test_login_starts_authorization_flow(schwab_env, test_client: TestClient):
    response = test_client.post("/login", json=LOGIN_BODY)
    assert response.status_code == 303
    assert response.json()["detail"] == AUTH_URL
    assert main.IN_APP_CONFIG.pending_schwab_response is schwab_env["contexts"][0]


def test_resubmit_without_wait_flag_reuses_pending_context(
    schwab_env, test_client: TestClient
):
    """The hang regression.

    A client that lost track of the authorization URL - and so omits
    wait_for_external_auth - must not cause a second context to be minted. The
    first context's callback server owns the port, so only that context can ever
    be redeemed.
    """
    test_client.post("/login", json=LOGIN_BODY)

    response = test_client.post("/login", json={**LOGIN_BODY, "force": True})

    assert response.status_code == 303
    assert response.json()["detail"] == AUTH_URL
    assert len(schwab_env["contexts"]) == 1, "a second login context was created"
    assert main.IN_APP_CONFIG.pending_schwab_response is schwab_env["contexts"][0]


def test_login_completes_against_the_original_context(
    schwab_env, test_client: TestClient
):
    test_client.post("/login", json=LOGIN_BODY)
    first = schwab_env["contexts"][0]

    response = test_client.post(
        "/login", json={**LOGIN_BODY, "force": True, "wait_for_external_auth": True}
    )

    assert response.status_code == 200
    assert schwab_env["fetched"] == [first]
    cached = main.IN_APP_CONFIG.provider_cache[ProviderType.SCHWAB]
    assert isinstance(cached, DummySchwabProvider) and cached.external_auth
    assert main.IN_APP_CONFIG.pending_schwab_response is None


def test_dead_callback_server_is_replaced(schwab_env, test_client: TestClient):
    """A context whose server died is unusable, so a fresh one is issued."""
    test_client.post("/login", json=LOGIN_BODY)
    first = schwab_env["contexts"][0]
    schwab_env["live"] = False

    response = test_client.post("/login", json={**LOGIN_BODY, "force": True})

    assert response.status_code == 303
    assert schwab_env["discarded"] == [first]
    assert len(schwab_env["contexts"]) == 2
    assert main.IN_APP_CONFIG.pending_schwab_response is schwab_env["contexts"][1]
