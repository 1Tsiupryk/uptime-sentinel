from datetime import datetime, timedelta, timezone
from unittest.mock import Mock
import logging
import pytest
from sqlalchemy.orm import Session, sessionmaker

from app.models import CheckResult, Monitor
import logging
import signal

from threading import Event
from types import SimpleNamespace
from unittest.mock import Mock

from app.worker.run import (
    is_monitor_due,
    main,
    run_check_cycle,
    run_worker,
)

def make_monitor(interval_seconds: int = 60, enabled: bool = True) -> Monitor:
    return Monitor(
        name="Example",
        url="https://example.com",
        interval_seconds=interval_seconds,
        timeout_seconds=5,
        expected_status_code=200,
        enabled=enabled,
    )


def make_result(
    checked_at: datetime,
    monitor_id: int = 1,
) -> CheckResult:
    return CheckResult(
        monitor_id=monitor_id,
        status="up",
        status_code=200,
        latency_ms=25,
        error=None,
        checked_at=checked_at,
    )
def test_monitor_without_results_is_due() -> None:
    monitor = make_monitor()

    assert is_monitor_due(monitor, None) is True

def test_recently_checked_monitor_is_not_due() -> None:
    now = datetime(2026, 8, 21, 12, 0, tzinfo=timezone.utc)
    monitor = make_monitor(interval_seconds=60)
    result = make_result(now - timedelta(seconds=30))

    assert is_monitor_due(monitor, result, now=now) is False

def test_monitor_is_due_after_interval() -> None:
    now = datetime(2026, 8, 21, 12, 0, tzinfo=timezone.utc)
    monitor = make_monitor(interval_seconds=60)
    result = make_result(now - timedelta(seconds=60))

    assert is_monitor_due(monitor, result, now=now) is True

def test_monitor_due_handles_naive_checked_at() -> None:
    now = datetime(2026, 8, 21, 12, 0, tzinfo=timezone.utc)
    monitor = make_monitor(interval_seconds=60)

    result = make_result(
        datetime(2026, 8, 21, 11, 59, 30)
    )

    assert is_monitor_due(monitor, result, now=now) is False

def fake_check_result(monitor_id: int) -> CheckResult:
    return CheckResult(
        monitor_id=monitor_id,
        status="up",
        status_code=200,
        latency_ms=20,
        error=None,
    )

def test_cycle_checks_enabled_monitor_without_history(
    db_session_factory: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch
) -> None:
    with db_session_factory() as db:
        monitor = make_monitor(enabled=True)
        db.add(monitor)
        db.commit()
        db.refresh(monitor)
        monitor_id = monitor.id

    checked_monitor_ids: list[int] = []

    def fake_run_monitor_check(
        monitor: Monitor,
        db: Session,
    ) -> CheckResult:
        checked_monitor_ids.append(monitor.id)
        return fake_check_result(monitor.id)

    monkeypatch.setattr(
        "app.worker.run.run_monitor_check",
        fake_run_monitor_check,
    )

    run_check_cycle(db_session_factory)

    assert checked_monitor_ids == [monitor_id]

def test_cycle_skips_disabled_monitor(
    db_session_factory: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch
) -> None:
    with db_session_factory() as db:
        db.add(make_monitor(enabled=False))
        db.commit()

    mock_runner = Mock()

    monkeypatch.setattr(
        "app.worker.run.run_monitor_check",
        mock_runner,
    )

    run_check_cycle(db_session_factory)

    mock_runner.assert_not_called()

def test_cycle_skips_monitor_that_is_not_due(
    db_session_factory: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with db_session_factory() as db:
        monitor = make_monitor(interval_seconds=60)
        db.add(monitor)
        db.commit()
        db.refresh(monitor)

        db.add(
            make_result(
                checked_at=datetime.now(timezone.utc),
                monitor_id=monitor.id,
            )
        )
        db.commit()

    mock_runner = Mock()

    monkeypatch.setattr(
        "app.worker.run.run_monitor_check",
        mock_runner,
    )

    run_check_cycle(db_session_factory)

    mock_runner.assert_not_called()

def test_cycle_continues_after_monitor_failure(
    db_session_factory: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    with db_session_factory() as db:
        first_monitor = make_monitor()
        second_monitor = make_monitor()

        first_monitor.name = "First"
        second_monitor.name = "Second"

        db.add_all([first_monitor, second_monitor])
        db.commit()
        db.refresh(first_monitor)
        db.refresh(second_monitor)

        monitor_ids = {first_monitor.id, second_monitor.id}

    attempted_monitor_ids: list[int] = []

    def fake_run_monitor_check(
        monitor: Monitor,
        db: Session,
    ) -> CheckResult:
        attempted_monitor_ids.append(monitor.id)

        if len(attempted_monitor_ids) == 1:
            raise RuntimeError("Simulated check failure")

        return fake_check_result(monitor.id)

    monkeypatch.setattr(
        "app.worker.run.run_monitor_check",
        fake_run_monitor_check,
    )

    caplog.set_level(
        logging.INFO,
        logger="app.worker.run",
    )

    run_check_cycle(db_session_factory)

    assert set(attempted_monitor_ids) == monitor_ids
    assert len(attempted_monitor_ids) == 2
    assert "Monitor check failed" in caplog.text
    assert "checked=1 skipped=0 failed=1" in caplog.text

def test_worker_runs_cycle_until_stopped(
    db_session_factory: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch
) -> None:
    stop_event = Event()
    received_factories: list[sessionmaker[Session]] = []

    def fake_run_check_cycle(session_factory: sessionmaker[Session]) -> None:
        received_factories.append(session_factory)
        stop_event.set()

    monkeypatch.setattr(
        "app.worker.run.run_check_cycle",
        fake_run_check_cycle
    )

    run_worker(
        stop_event=stop_event,
        poll_interval_seconds=60,
        session_factory=db_session_factory,
    )

    assert received_factories == [db_session_factory]
    assert stop_event.is_set()

class ImmediateEvent(Event):
    def wait(self, timeout: float | None = None) -> bool:
        return super().wait(0)

def test_worker_continues_after_cycle_failure(
    db_session_factory: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    stop_event = ImmediateEvent()
    attempt_count = 0

    def fake_run_check_cycle(
        session_factory: sessionmaker[Session],
    ) -> None:
        nonlocal attempt_count
        attempt_count += 1

        if attempt_count == 1:
            raise RuntimeError("Database temporarily unavailable")

        stop_event.set()

    monkeypatch.setattr("app.worker.run.run_check_cycle", fake_run_check_cycle)
    caplog.set_level(logging.INFO, logger="app.worker.run")

    run_worker(
        stop_event=stop_event,
        poll_interval_seconds=5,
        session_factory=db_session_factory
    )

    assert attempt_count == 2
    assert "Worker cycle failed" in caplog.text
    assert "Worker stopped" in caplog.text

def test_main_registers_shutdown_handlers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stop_event = Mock(spec=Event)
    mock_signal = Mock()
    mock_run_worker = Mock()
    mock_configure_logging = Mock()

    settings = SimpleNamespace(
        WORKER_POLL_INTERVAL_SECONDS=7
    )

    monkeypatch.setattr("app.worker.run.Event", Mock(return_value=stop_event))
    monkeypatch.setattr("app.worker.run.signal.signal", mock_signal)
    monkeypatch.setattr("app.worker.run.get_settings", Mock(return_value=settings))
    monkeypatch.setattr("app.worker.run.run_worker", mock_run_worker)
    monkeypatch.setattr("app.worker.run.configure_logging", mock_configure_logging)

    main()

    mock_configure_logging.assert_called_once()

    registered_handlers = {
        call.args[0]: call.args[1]
        for call in mock_signal.call_args_list
    }

    assert signal.SIGTERM in registered_handlers
    assert signal.SIGINT in registered_handlers

    mock_run_worker.assert_called_once_with(
        stop_event=stop_event,
        poll_interval_seconds=7
    )

    registered_handlers[signal.SIGTERM](
        signal.SIGTERM,
        None,
    )

    stop_event.set.assert_called_once()