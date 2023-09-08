import sys
from os.path import dirname

sys.path.insert(0, dirname(dirname(__file__)))


import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def test_client():
    yield TestClient(app)
