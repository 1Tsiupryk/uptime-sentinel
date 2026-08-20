from httpcore import request
from _pytest import assertion
from unittest.mock import Mock

import httpx
import pytest

from app.models import Monitor
from app.services.checker import check_monitor

def make_monitor(expected_status_code: int = 200, timeout_seconds: int = 5) -> Monitor:
    return Monitor(
        name="Example",
        url="https://example.com",
        interval_seconds=60,
        timeout_seconds=timeout_seconds,
        expected_status_code=expected_status_code,
        enabled=True,
    )

def test_check_monitor_returns_up_for_expected_status(monkeypatch: pytest.MonkeyPatch) -> None:
    monitor = make_monitor(expected_status_code=200)

    mock_get = Mock(return_value=httpx.Response(status_code=200))
    monkeypatch.setattr("app.services.checker.httpx.get", mock_get)

    outcome = check_monitor(monitor)

    assert outcome.status == "up"
    assert outcome.status_code == 200
    assert outcome.error is None
    assert outcome.latency_ms >= 0

    mock_get.assert_called_once_with("https://example.com", timeout=5, follow_redirects=False)



def test_check_monitor_returns_down_for_unexpected_status(monkeypatch: pytest.MonkeyPatch) -> None:
    monitor = make_monitor(expected_status_code=200)

    mock_get = Mock(return_value=httpx.Response(status_code=500))
    monkeypatch.setattr("app.services.checker.httpx.get", mock_get)

    outcome = check_monitor(monitor)

    assert outcome.status == "down"
    assert outcome.status_code == 500
    assert outcome.latency_ms >= 0
    assert outcome.error == "Expected status 200, received 500"


def test_check_monitor_handles_connection_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monitor = make_monitor()

    request = httpx.Request("GET", monitor.url)
    connection_error = httpx.ConnectError("Connection refused", request=request)

    mock_get = Mock(side_effect=connection_error)
    monkeypatch.setattr("app.services.checker.httpx.get", mock_get)

    outcome = check_monitor(monitor)

    assert outcome.status == "down"
    assert outcome.status_code is None
    assert outcome.latency_ms >= 0
    assert outcome.error is not None
    assert "ConnectError" in outcome.error
    assert "Connection refused" in outcome.error


def test_check_monitor_handles_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    monitor = make_monitor(timeout_seconds=2)

    request = httpx.Request("GET", monitor.url)
    timeout_error = httpx.ReadTimeout("Request timed out", request=request)

    mock_get = Mock(side_effect=timeout_error)
    monkeypatch.setattr("app.services.checker.httpx.get", mock_get)

    outcome = check_monitor(monitor)

    assert outcome.status == "down"
    assert outcome.status_code is None
    assert outcome.latency_ms >= 0
    assert outcome.error is not None
    assert "ReadTimeout" in outcome.error

    mock_get.assert_called_once_with("https://example.com", timeout=2, follow_redirects=False)