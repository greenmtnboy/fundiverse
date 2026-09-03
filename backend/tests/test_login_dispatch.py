"""Coverage for the provider login registry.

login() dispatches through PROVIDER_LOGINS rather than a chain of branches, so
the thing worth guarding is that the registry stays in step with the providers
the API actually advertises.
"""

from fastapi.testclient import TestClient
from py_portfolio_index import AVAILABLE_PROVIDERS
from py_portfolio_index.enums import ProviderType

import main


def test_every_advertised_provider_can_log_in():
    """The /providers list and the login registry must not drift apart.

    A provider the UI offers but login() cannot dispatch would present a working
    login form that always 404s.
    """
    missing = [p.value for p in AVAILABLE_PROVIDERS if p not in main.PROVIDER_LOGINS]
    assert not missing, f"advertised but not loggable: {missing}"


def test_registry_holds_no_unadvertised_providers():
    extra = [p.value for p in main.PROVIDER_LOGINS if p not in AVAILABLE_PROVIDERS]
    assert not extra, f"loggable but not advertised: {extra}"


def test_unsupported_provider_is_rejected(test_client: TestClient):
    assert ProviderType.DUMMY not in main.PROVIDER_LOGINS

    response = test_client.post(
        "/login", json={"key": "k", "secret": "s", "provider": ProviderType.DUMMY.value}
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Selected provider not supported yet"
