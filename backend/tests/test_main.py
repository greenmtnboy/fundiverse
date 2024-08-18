from fastapi.testclient import TestClient
from datetime import datetime
from py_portfolio_index.models import IdealPortfolio


def test_read_main(test_client: TestClient):
    # we skip validation outside pyinstaller bundles
    # so set manually here
    test_client.app.in_app_config.validate = True  # type: ignore
    response = test_client.get("/")
    assert response.status_code == 401
    test_client.app.in_app_config.validate = False  # type: ignore


def test_async_functions(test_client: TestClient):
    response = test_client.post("/long_sleep", json={"sleep": 1})
    assert response.status_code == 200
    assert response.json().get("slept") == 1

    ## start async test
    response = test_client.post("/async_long_sleep", json={"sleep": 5})
    assert response.status_code == 200

    guid1 = response.json().get("guid")
    assert guid1 is not None

    response = test_client.post("/async_long_sleep", json={"sleep": 5})
    assert response.status_code == 200
    guid2 = response.json().get("guid")
    assert guid2 is not None

    datetime1 = datetime.now()

    found: set[str] = set()
    attempts = 0
    max_attempts = 5
    from time import sleep

    while len(found) < 2:
        attempts += 1
        for guid in (guid1, guid2):
            if guid in found:
                continue
            response = test_client.get(f"/background_tasks/{guid}")
            print(response)
            if response.status_code == 200:
                found.add(guid)
                assert response.json().get("slept") == 5
                break
            elif response.status_code == 102:
                pass
            else:
                raise ValueError(response)
        sleep(1)
        if attempts > max_attempts:
            raise ValueError(f"Too many attempts, last response {response}")
    # basic check that they ran async and not 5+5 seconds
    assert (datetime.now() - datetime1).seconds < 7


def test_index_to_processed_index(test_client: TestClient):
    test_input = {
        "index": "total_market",
        "stock_exclusions": ["META", "BRK.A", "NEE", "WFC", "FOX", "TWTR", "TSLA"],
        "list_exclusions": [
            "vice",
            "cruises",
            "non_ethical_conduct",
            "coal",
            "oil",
            "meat_poultry",
        ],
        "stock_modifications": [{"ticker": "SPOT", "scale": 2, "minWeight": None}],
        "list_modifications": [{"list": "renewable", "scale": 1.5}],
        "reweight": False,
    }
    index = test_client.post("/generate_index", json=test_input)

    assert index.status_code == 200

    response = IdealPortfolio.model_validate(index.json())

    for x in response.holdings:
        if x.ticker == "TSLA":
            raise SyntaxError("TSLA should be excluded")
            assert x.weight == 0
