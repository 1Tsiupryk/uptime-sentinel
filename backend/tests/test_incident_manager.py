from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.models import CheckResult, Incident, Monitor
from app.services.incident_manager import process_check_result


def create_monitor(db: Session) -> Monitor:
    monitor = Monitor(
        name="Example",
        url="https://example.com",
        interval_seconds=60,
        timeout_seconds=5,
        expected_status_code=200,
        enabled=True,
    )
    db.add(monitor)
    db.flush()

    return monitor


def create_check_result(
    db: Session,
    monitor_id: int,
    status: str,
) -> CheckResult:
    is_up = status == "up"
    check_result = CheckResult(
        monitor_id=monitor_id,
        status=status,
        status_code=200 if is_up else 500,
        latency_ms=25,
        error=None if is_up else "Expected status 200, received 500",
        checked_at=datetime.now(timezone.utc),
    )
    db.add(check_result)
    db.flush()

    return check_result


def test_down_check_creates_incident(
    db_session_factory: sessionmaker[Session],
) -> None:
    with db_session_factory() as db:
        monitor = create_monitor(db)
        down_check = create_check_result(db, monitor.id, "down")

        incident = process_check_result(db, down_check)
        db.commit()

        incidents = db.scalars(select(Incident)).all()

        assert incident is not None
        assert len(incidents) == 1
        assert incidents[0].monitor_id == monitor.id
        assert incidents[0].opening_check_id == down_check.id
        assert incidents[0].started_at == down_check.checked_at
        assert incidents[0].resolved_at is None
        assert incidents[0].closing_check_id is None


def test_repeated_down_check_does_not_create_another_incident(
    db_session_factory: sessionmaker[Session],
) -> None:
    with db_session_factory() as db:
        monitor = create_monitor(db)
        first_down_check = create_check_result(db, monitor.id, "down")
        first_incident = process_check_result(db, first_down_check)

        second_down_check = create_check_result(db, monitor.id, "down")
        returned_incident = process_check_result(db, second_down_check)
        db.commit()

        incidents = db.scalars(select(Incident)).all()

        assert first_incident is not None
        assert returned_incident is not None
        assert len(incidents) == 1
        assert returned_incident.id == first_incident.id
        assert incidents[0].opening_check_id == first_down_check.id
        assert incidents[0].resolved_at is None
        assert incidents[0].closing_check_id is None


def test_up_check_resolves_open_incident(
    db_session_factory: sessionmaker[Session],
) -> None:
    with db_session_factory() as db:
        monitor = create_monitor(db)
        down_check = create_check_result(db, monitor.id, "down")
        process_check_result(db, down_check)

        up_check = create_check_result(db, monitor.id, "up")
        resolved_incident = process_check_result(db, up_check)
        db.commit()

        incident = db.scalar(select(Incident))
        persisted_up_check = db.get(CheckResult, up_check.id)

        assert resolved_incident is not None
        assert incident is not None
        assert persisted_up_check is not None
        assert incident.resolved_at == persisted_up_check.checked_at
        assert incident.closing_check_id == persisted_up_check.id


def test_up_check_without_open_incident_does_nothing(
    db_session_factory: sessionmaker[Session],
) -> None:
    with db_session_factory() as db:
        monitor = create_monitor(db)
        up_check = create_check_result(db, monitor.id, "up")

        incident = process_check_result(db, up_check)
        db.commit()

        incidents = db.scalars(select(Incident)).all()

        assert incident is None
        assert incidents == []
