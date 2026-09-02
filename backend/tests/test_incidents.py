from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.models import CheckResult, Incident, Monitor


def create_monitor(db: Session, name: str = "Example") -> int:
    monitor = Monitor(
        name=name,
        url="https://example.com",
        interval_seconds=60,
        timeout_seconds=5,
        expected_status_code=200,
        enabled=True,
    )
    db.add(monitor)
    db.flush()

    return monitor.id


def create_incident(
    db: Session,
    monitor_id: int,
    started_at: datetime,
    *,
    resolved: bool = False,
) -> int:
    opening_check = CheckResult(
        monitor_id=monitor_id,
        status="down",
        status_code=500,
        latency_ms=25,
        error="Expected status 200, received 500",
        checked_at=started_at,
    )
    db.add(opening_check)
    db.flush()

    incident = Incident(
        monitor_id=monitor_id,
        started_at=started_at,
        opening_check_id=opening_check.id,
    )

    if resolved:
        resolved_at = started_at + timedelta(minutes=5)
        closing_check = CheckResult(
            monitor_id=monitor_id,
            status="up",
            status_code=200,
            latency_ms=20,
            error=None,
            checked_at=resolved_at,
        )
        db.add(closing_check)
        db.flush()

        incident.resolved_at = resolved_at
        incident.closing_check_id = closing_check.id

    db.add(incident)
    db.flush()

    return incident.id


def test_get_incidents_returns_newest_first(
    client: TestClient,
    db_session_factory: sessionmaker[Session],
) -> None:
    with db_session_factory() as db:
        monitor_id = create_monitor(db)
        older_incident_id = create_incident(
            db,
            monitor_id,
            datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc),
            resolved=True,
        )
        newer_incident_id = create_incident(
            db,
            monitor_id,
            datetime(2026, 9, 2, 10, 0, tzinfo=timezone.utc),
        )
        db.commit()

    response = client.get("/incidents")

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [
        newer_incident_id,
        older_incident_id,
    ]


def test_get_incidents_filters_by_status(
    client: TestClient,
    db_session_factory: sessionmaker[Session],
) -> None:
    with db_session_factory() as db:
        monitor_id = create_monitor(db)
        resolved_incident_id = create_incident(
            db,
            monitor_id,
            datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc),
            resolved=True,
        )
        open_incident_id = create_incident(
            db,
            monitor_id,
            datetime(2026, 9, 2, 10, 0, tzinfo=timezone.utc),
        )
        db.commit()

    open_response = client.get("/incidents", params={"status": "open"})
    resolved_response = client.get(
        "/incidents",
        params={"status": "resolved"},
    )

    assert open_response.status_code == 200
    assert [item["id"] for item in open_response.json()] == [open_incident_id]

    assert resolved_response.status_code == 200
    assert [item["id"] for item in resolved_response.json()] == [
        resolved_incident_id
    ]


def test_get_incident_returns_incident(
    client: TestClient,
    db_session_factory: sessionmaker[Session],
) -> None:
    with db_session_factory() as db:
        monitor_id = create_monitor(db)
        incident_id = create_incident(
            db,
            monitor_id,
            datetime(2026, 9, 2, 10, 0, tzinfo=timezone.utc),
        )
        db.commit()

    response = client.get(f"/incidents/{incident_id}")

    assert response.status_code == 200
    assert response.json()["id"] == incident_id
    assert response.json()["monitor_id"] == monitor_id
    assert response.json()["resolved_at"] is None
    assert response.json()["closing_check_id"] is None


def test_get_missing_incident_returns_404(client: TestClient) -> None:
    response = client.get("/incidents/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Incident not found"}


def test_get_monitor_incidents_returns_only_requested_monitor_history(
    client: TestClient,
    db_session_factory: sessionmaker[Session],
) -> None:
    with db_session_factory() as db:
        first_monitor_id = create_monitor(db, "First")
        second_monitor_id = create_monitor(db, "Second")

        older_incident_id = create_incident(
            db,
            first_monitor_id,
            datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc),
            resolved=True,
        )
        newer_incident_id = create_incident(
            db,
            first_monitor_id,
            datetime(2026, 9, 2, 10, 0, tzinfo=timezone.utc),
        )
        create_incident(
            db,
            second_monitor_id,
            datetime(2026, 9, 2, 11, 0, tzinfo=timezone.utc),
        )
        db.commit()

    response = client.get(f"/monitors/{first_monitor_id}/incidents")

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [
        newer_incident_id,
        older_incident_id,
    ]
    assert all(
        item["monitor_id"] == first_monitor_id
        for item in response.json()
    )


def test_get_incidents_for_missing_monitor_returns_404(
    client: TestClient,
) -> None:
    response = client.get("/monitors/999/incidents")

    assert response.status_code == 404
    assert response.json() == {"detail": "Monitor not found"}
