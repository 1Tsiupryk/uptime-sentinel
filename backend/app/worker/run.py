from datetime import datetime, timedelta, timezone
import logging

from app.db import SessionLocal
from app.models import Monitor, CheckResult
from app.services.check_runner import run_monitor_check

from sqlalchemy.orm import Session, sessionmaker

import signal

from threading import Event
from types import FrameType

from app.config import get_settings

logger = logging.getLogger(__name__)

def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s"
    )

def normalize_to_utc(value: datetime) -> datetime:
    """Return a timezone-aware datetime normalized to UTC."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)

def is_monitor_due(
    monitor: Monitor,
    last_result: CheckResult | None,
    *,
    now: datetime | None = None,
) -> bool:
    """Return whether a monitor is due for its next scheduled check."""

    if last_result is None:
        return True

    current_time = normalize_to_utc(now or datetime.now(timezone.utc))
    checked_at = normalize_to_utc(last_result.checked_at)

    return current_time - checked_at >= timedelta(seconds=monitor.interval_seconds)


def run_check_cycle(session_factory: sessionmaker[Session] = SessionLocal) -> None:

    checked_count = 0
    skipped_count = 0
    failed_count = 0

    with session_factory() as db:
        monitors = db.query(Monitor).filter(Monitor.enabled.is_(True)).all()
        logger.debug("Worker cycle started enabled_monitors=%s", len(monitors))

        for monitor in monitors:
            last_check_result = (
                db.query(CheckResult)
                .filter(CheckResult.monitor_id == monitor.id)
                .order_by(
                    CheckResult.checked_at.desc(),
                    CheckResult.id.desc()
                )
                .first()
            )

            if not is_monitor_due(monitor, last_check_result):
                logger.debug("Monitor is not due monitor_id=%s", monitor.id)
                skipped_count += 1
                continue
            
            logger.info("Monitor check started monitor_id=%s name=%s", monitor.id, monitor.name)

            try:
                check_result = run_monitor_check(monitor, db)
                checked_count += 1
            except Exception:
                db.rollback()
                failed_count += 1
                logger.exception(
                    "Monitor check failed monitor_id=%s",
                    monitor.id,
                )
                continue

            logger.info(
                "Monitor check completed monitor_id=%s status=%s status_code=%s latency_ms=%s",
                monitor.id,
                check_result.status,
                check_result.status_code,
                check_result.latency_ms
            )
                

    if checked_count or failed_count:
        logger.info(
            "Worker cycle completed checked=%s skipped=%s failed=%s",
            checked_count,
            skipped_count,
            failed_count
        )
    else:
        logger.debug(
            "Worker cycle completed checked=%s skipped=%s failed=%s",
            checked_count,
            skipped_count,
            failed_count
        )


def run_worker(
    stop_event: Event,
    poll_interval_seconds: int,
    session_factory: sessionmaker[Session] = SessionLocal
) -> None:
    """Run check cycles until a shutdown signal is received."""
    logger.info("Worker started poll_interval_seconds=%s", poll_interval_seconds)

    while not stop_event.is_set():
        try:
            run_check_cycle(session_factory)
        except Exception:
            logger.exception("Worker cycle failed")

        stop_event.wait(poll_interval_seconds)

    logger.info("Worker stopped")

def main() -> None:
    """Configure and start the background worker."""
    configure_logging()

    settings = get_settings()
    stop_event = Event()

    def request_shutdown(signum: int, _frame: FrameType | None) -> None:
        signal_name = signal.Signals(signum).name
        logger.info("Worker shutdown requested signal=%s", signal_name)

        stop_event.set()

    signal.signal(signal.SIGTERM, request_shutdown)
    signal.signal(signal.SIGINT, request_shutdown)

    run_worker(
        stop_event=stop_event,
        poll_interval_seconds=settings.WORKER_POLL_INTERVAL_SECONDS
    )

if __name__ == "__main__":
    main()