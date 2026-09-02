from unittest.mock import Mock

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.models import CheckResult, Incident, Monitor
from app.services.check_runner import run_monitor_check
from app.services.checker import CheckOutcome


def create_monitor(db: Session, name: str = "Example") -> Monitor:
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

    return monitor


def down_outcome() -> CheckOutcome:
    return CheckOutcome(
        status="down",
        status_code=500,
        latency_ms=25,
        error="Expected status 200, received 500",
    )


def up_outcome() -> CheckOutcome:
    return CheckOutcome(
        status="up",
        status_code=200,
        latency_ms=20,
        error=None,
    )


def test_down_check_creates_result_and_opens_incident(
    db_session_factory: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock_check = Mock(return_value=down_outcome())
    monkeypatch.setattr("app.services.check_runner.check_monitor", mock_check)

    with db_session_factory() as db:
        monitor = create_monitor(db)

        check_result = run_monitor_check(monitor, db)
        incident = db.scalar(select(Incident))

        assert incident is not None
        assert check_result.status == "down"
        assert check_result.status_code == 500
        assert incident.monitor_id == monitor.id
        assert incident.opening_check_id == check_result.id
        assert incident.started_at == check_result.checked_at
        assert incident.resolved_at is None
        assert incident.closing_check_id is None
        mock_check.assert_called_once_with(monitor)


def test_repeated_down_check_does_not_open_duplicate_incident(
    db_session_factory: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock_check = Mock(side_effect=[down_outcome(), down_outcome()])
    monkeypatch.setattr("app.services.check_runner.check_monitor", mock_check)

    with db_session_factory() as db:
        monitor = create_monitor(db)

        first_check = run_monitor_check(monitor, db)
        second_check = run_monitor_check(monitor, db)

        checks = db.scalars(
            select(CheckResult).order_by(CheckResult.id),
        ).all()
        incidents = db.scalars(select(Incident)).all()

        assert len(checks) == 2
        assert len(incidents) == 1
        assert incidents[0].opening_check_id == first_check.id
        assert incidents[0].opening_check_id != second_check.id
        assert incidents[0].resolved_at is None
        assert mock_check.call_count == 2


def test_up_check_resolves_incident_opened_by_previous_down_check(
    db_session_factory: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock_check = Mock(side_effect=[down_outcome(), up_outcome()])
    monkeypatch.setattr("app.services.check_runner.check_monitor", mock_check)

    with db_session_factory() as db:
        monitor = create_monitor(db)

        down_check = run_monitor_check(monitor, db)
        up_check = run_monitor_check(monitor, db)
        incident = db.scalar(select(Incident))

        assert incident is not None
        assert incident.opening_check_id == down_check.id
        assert incident.closing_check_id == up_check.id
        assert incident.resolved_at == up_check.checked_at
        assert mock_check.call_count == 2


def test_incidents_are_isolated_between_monitors(
    db_session_factory: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock_check = Mock(side_effect=[down_outcome(), down_outcome()])
    monkeypatch.setattr("app.services.check_runner.check_monitor", mock_check)

    with db_session_factory() as db:
        first_monitor = create_monitor(db, "First monitor")
        second_monitor = create_monitor(db, "Second monitor")

        first_check = run_monitor_check(first_monitor, db)
        second_check = run_monitor_check(second_monitor, db)

        incidents = db.scalars(
            select(Incident).order_by(Incident.monitor_id),
        ).all()

        assert len(incidents) == 2
        assert incidents[0].monitor_id == first_monitor.id
        assert incidents[0].opening_check_id == first_check.id
        assert incidents[1].monitor_id == second_monitor.id
        assert incidents[1].opening_check_id == second_check.id

