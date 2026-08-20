from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from app.services.checker import CheckOutcome

def create_monitor(client: TestClient) -> int:
    response = client.post(
        "/monitors",
        json={
            "name": "Example Website",
            "url": "https://example.com",
        },
    )

    assert response.status_code == 201

    return response.json()["id"]

def test_trigger_check_creates_result(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monitor_id = create_monitor(client)

    mock_check = Mock(
        return_value=CheckOutcome(
            status="up",
            status_code=200,
            latency_ms=42,
            error=None,
        )
    )

    monkeypatch.setattr(
        "app.api.checks.check_monitor",
        mock_check,
    )

    response = client.post(f"/monitors/{monitor_id}/check")

    assert response.status_code == 201

    data = response.json()

    assert data["monitor_id"] == monitor_id
    assert data["status"] == "up"
    assert data["status_code"] == 200
    assert data["latency_ms"] == 42
    assert data["error"] is None
    assert data["checked_at"] is not None
    assert isinstance(data["id"], int)

    mock_check.assert_called_once()

def test_trigger_check_for_missing_monitor_returns_404(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    mock_check = Mock()
    monkeypatch.setattr("app.api.checks.check_monitor", mock_check)

    response = client.post("/monitors/999/check")

    assert response.status_code == 404
    assert response.json() == {"detail": "Monitor not found"}
    mock_check.assert_not_called()

def test_get_checks_returns_empty_list(client: TestClient) -> None:
    monitor_id = create_monitor(client)

    response = client.get(f"/monitors/{monitor_id}/checks")

    assert response.status_code == 200
    assert response.json() == []

def test_get_checks_returns_newest_first(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monitor_id = create_monitor(client)

    mock_check = Mock(
        side_effect=[
            CheckOutcome(
                status="down",
                status_code=500,
                latency_ms=100,
                error="Expected status 200, received 500",
            ),
            CheckOutcome(
                status="up",
                status_code=200,
                latency_ms=40,
                error=None,
            ),
        ]
    )

    monkeypatch.setattr(
        "app.api.checks.check_monitor",
        mock_check,
    )

    first_response = client.post(f"/monitors/{monitor_id}/check")
    second_response = client.post(f"/monitors/{monitor_id}/check")

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    response = client.get(f"/monitors/{monitor_id}/checks")

    assert response.status_code == 200

    checks = response.json()

    assert len(checks) == 2

    assert checks[0]["status"] == "up"
    assert checks[0]["status_code"] == 200
    assert checks[0]["latency_ms"] == 40

    assert checks[1]["status"] == "down"
    assert checks[1]["status_code"] == 500
    assert checks[1]["error"] == "Expected status 200, received 500"

    assert checks[0]["id"] > checks[1]["id"]

def test_get_checks_for_missing_monitor_returns_404(client: TestClient) -> None:
    response = client.get("/monitors/999/checks")

    assert response.status_code == 404
    assert response.json() == {"detail": "Monitor not found"}