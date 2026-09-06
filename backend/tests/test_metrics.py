from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY

from app.metrics import record_check, record_incident_event
from app.services.checker import CheckOutcome


def metric_value(
    name: str,
    labels: dict[str, str],
) -> float:
    return REGISTRY.get_sample_value(name, labels) or 0.0


def test_metrics_endpoint_returns_prometheus_format(
    client: TestClient,
) -> None:
    response = client.get("/metrics")

    assert response.status_code == 200
    assert response.headers["content-type"] == CONTENT_TYPE_LATEST
    assert "uptime_sentinel_checks_total" in response.text
    assert "uptime_sentinel_check_latency_seconds" in response.text
    assert "uptime_sentinel_incident_events_total" in response.text


def test_record_check_updates_counter_and_histogram() -> None:
    labels = {
        "monitor_id": "999999",
        "status": "down",
    }
    histogram_labels = {"monitor_id": "999999"}

    checks_before = metric_value(
        "uptime_sentinel_checks_total",
        labels,
    )
    observations_before = metric_value(
        "uptime_sentinel_check_latency_seconds_count",
        histogram_labels,
    )
    latency_before = metric_value(
        "uptime_sentinel_check_latency_seconds_sum",
        histogram_labels,
    )

    record_check(
        monitor_id=999999,
        status="down",
        latency_ms=250,
    )

    assert metric_value(
        "uptime_sentinel_checks_total",
        labels,
    ) == checks_before + 1

    assert metric_value(
        "uptime_sentinel_check_latency_seconds_count",
        histogram_labels,
    ) == observations_before + 1

    assert metric_value(
        "uptime_sentinel_check_latency_seconds_sum",
        histogram_labels,
    ) == pytest.approx(latency_before + 0.25)


def test_record_incident_event_updates_counter() -> None:
    labels = {"event": "opened"}

    events_before = metric_value(
        "uptime_sentinel_incident_events_total",
        labels,
    )

    record_incident_event("opened")

    assert metric_value(
        "uptime_sentinel_incident_events_total",
        labels,
    ) == events_before + 1


def create_monitor(client: TestClient) -> int:
    response = client.post(
        "/monitors",
        json={
            "name": "Metrics test monitor",
            "url": "https://example.com",
        },
    )

    assert response.status_code == 201
    return response.json()["id"]


def test_metrics_endpoint_uses_latest_monitor_status(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monitor_id = create_monitor(client)
    mock_check = Mock(
        side_effect=[
            CheckOutcome(
                status="down",
                status_code=500,
                latency_ms=25,
                error="Expected status 200, received 500",
            ),
            CheckOutcome(
                status="up",
                status_code=200,
                latency_ms=20,
                error=None,
            ),
        ],
    )
    monkeypatch.setattr(
        "app.services.check_runner.check_monitor",
        mock_check,
    )

    first_check = client.post(f"/monitors/{monitor_id}/check")
    second_check = client.post(f"/monitors/{monitor_id}/check")

    assert first_check.status_code == 201
    assert second_check.status_code == 201

    response = client.get("/metrics")

    assert response.status_code == 200
    assert (
        f'uptime_sentinel_monitor_up{{monitor_id="{monitor_id}"}} 1.0'
        in response.text
    )


def test_metrics_endpoint_removes_deleted_monitor(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monitor_id = create_monitor(client)
    mock_check = Mock(
        return_value=CheckOutcome(
            status="up",
            status_code=200,
            latency_ms=20,
            error=None,
        ),
    )
    monkeypatch.setattr(
        "app.services.check_runner.check_monitor",
        mock_check,
    )

    check_response = client.post(f"/monitors/{monitor_id}/check")
    assert check_response.status_code == 201

    metric_line = (
        f'uptime_sentinel_monitor_up{{monitor_id="{monitor_id}"}} 1.0'
    )

    response_before_delete = client.get("/metrics")
    assert metric_line in response_before_delete.text

    delete_response = client.delete(f"/monitors/{monitor_id}")
    assert delete_response.status_code == 204

    response_after_delete = client.get("/metrics")
    assert metric_line not in response_after_delete.text
