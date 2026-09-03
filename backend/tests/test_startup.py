"""Coverage for server startup.

run() picks a serving strategy per environment, and both branches must hand
back something callable. An earlier version assigned uvicorn.run's *return
value* in the frozen branch - and since that assignment made `run` a local of
the enclosing function of the same name, the packaged app raised TypeError on
shutdown and never reached the graceful ShutdownException path at all.
"""

import sys

import pytest

import main


@pytest.fixture
def not_in_ci(monkeypatch):
    monkeypatch.delenv("IN_CI", raising=False)


@pytest.fixture
def frozen(monkeypatch, not_in_ci):
    """Look like a PyInstaller bundle."""
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", "meipass", raising=False)


@pytest.fixture
def dev(monkeypatch, not_in_ci):
    monkeypatch.delattr(sys, "frozen", raising=False)


def test_frozen_branch_serves_and_restores_stdout(frozen, monkeypatch):
    calls = []
    seen = {}

    def fake_run(app, **kwargs):
        calls.append((app, kwargs))
        seen["stdout"] = sys.stdout

    monkeypatch.setattr(main.uvicorn, "run", fake_run)
    before = sys.stdout

    main.run()

    assert len(calls) == 1, "the frozen branch never started a server"
    assert calls[0][0] is main.app
    assert seen["stdout"] is not before, "stdout was not silenced while serving"
    assert sys.stdout is before, "stdout was not restored after serving"


def test_frozen_shutdown_exception_exits_zero(frozen, monkeypatch):
    """A requested shutdown is graceful, not a crash.

    This also covers the shutdown handler printing after the devnull handle
    has been closed - it must not be writing to a closed stdout.
    """

    def fake_run(app, **kwargs):
        raise main.ShutdownException("Server is shutting down")

    monkeypatch.setattr(main.uvicorn, "run", fake_run)

    with pytest.raises(SystemExit) as excinfo:
        main.run()

    assert excinfo.value.code == 0


def test_frozen_unexpected_error_exits_nonzero(frozen, monkeypatch):
    def fake_run(app, **kwargs):
        raise ValueError("port already bound")

    monkeypatch.setattr(main.uvicorn, "run", fake_run)

    with pytest.raises(SystemExit) as excinfo:
        main.run()

    assert excinfo.value.code == 1


def test_dev_branch_serves_with_reload(dev, monkeypatch):
    calls = []
    monkeypatch.setattr(main.uvicorn, "run", lambda app, **kw: calls.append((app, kw)))

    main.run()

    assert len(calls) == 1, "the dev branch never started a server"
    assert calls[0][0] == "main:app"
    assert calls[0][1]["reload"] is True
