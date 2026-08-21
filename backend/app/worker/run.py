from datetime import datetime, timedelta, timezone
import logging
from app.db import SessionLocal
from app.models import Monitor, CheckResult
from app.services.check_runner import run_monitor_check
from redis import Redis
from redis.exceptions import LockNotOwnedError, RedisError
from app.redis_client import check_redis_connection, create_redis_client
from app.services.monitor_lock import try_acquire_monitor_lock
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

def get_last_check_result(db: Session, monitor_id: int) -> CheckResult | None:
    """Return the most recent check result for a monitor."""
    return (
        db.query(CheckResult)
        .filter(CheckResult.monitor_id == monitor_id)
        .order_by(
            CheckResult.checked_at.desc(),
            CheckResult.id.desc(),
        )
        .first()
    )


def run_check_cycle(redis_client: Redis, lock_timeout_seconds: int, session_factory: sessionmaker[Session] = SessionLocal) -> None:

    checked_count = 0
    skipped_count = 0
    failed_count = 0

    with session_factory() as db:
        monitors = db.query(Monitor).filter(Monitor.enabled.is_(True)).all()
        logger.debug("Worker cycle started enabled_monitors=%s", len(monitors))

        for monitor in monitors:
            last_check_result = get_last_check_result(db, monitor.id)

            if not is_monitor_due(monitor, last_check_result):
                logger.debug("Monitor is not due monitor_id=%s", monitor.id)
                skipped_count += 1
                continue

            try:
                lock = try_acquire_monitor_lock(
                    client=redis_client,
                    monitor_id=monitor.id,
                    timeout_seconds=lock_timeout_seconds,
                )
            except RedisError:
                logger.exception(
                    "Failed to acquire lock for monitor_id=%s",
                    monitor.id
                )
                failed_count += 1
                continue

            if lock is None:
                logger.debug(
                    "Monitor already being checked by another worker monitor_id=%s",
                    monitor.id
                )
                skipped_count += 1
                continue
                
            try:
                db.expire_all()

                latest_check_result = get_last_check_result(db, monitor.id)

                if not is_monitor_due(monitor, latest_check_result):
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
                        monitor.id
                    )
                    continue

                logger.info(
                    "Monitor check completed monitor_id=%s status=%s status_code=%s latency_ms=%s",
                    monitor.id,
                    check_result.status,
                    check_result.status_code,
                    check_result.latency_ms
                )

            finally:
                try:
                    lock.release()
                except LockNotOwnedError:
                    logger.error(
                        "Monitor lock expired before release monitor_id=%s",
                        monitor.id
                    )
                except RedisError:
                    logger.exception(
                        "Failed to release lock for monitor_id=%s",
                        monitor.id
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
    redis_client: Redis,
    lock_timeout_seconds: int,
    session_factory: sessionmaker[Session] = SessionLocal
) -> None:
    """Run check cycles until a shutdown signal is received."""
    logger.info("Worker started poll_interval_seconds=%s", poll_interval_seconds)

    while not stop_event.is_set():
        try:
            run_check_cycle(
                redis_client=redis_client,
                lock_timeout_seconds=lock_timeout_seconds,
                session_factory=session_factory
            )
        except Exception:
            logger.exception("Worker cycle failed")

        stop_event.wait(poll_interval_seconds)

    logger.info("Worker stopped")

def main() -> None:
    """Configure and start the background worker."""
    configure_logging()

    settings = get_settings()
    redis_client = create_redis_client(settings)

    if not check_redis_connection(redis_client):
        logger.error("Worker startup aborted because Redis is unavailable")
        redis_client.close()
        raise SystemExit(1)
        
    stop_event = Event()

    def request_shutdown(signum: int, _frame: FrameType | None) -> None:
        signal_name = signal.Signals(signum).name
        logger.info("Worker shutdown requested signal=%s", signal_name)

        stop_event.set()

    signal.signal(signal.SIGTERM, request_shutdown)
    signal.signal(signal.SIGINT, request_shutdown)
    try:
        run_worker(
            stop_event=stop_event,
            poll_interval_seconds=settings.WORKER_POLL_INTERVAL_SECONDS,
            redis_client=redis_client,
            lock_timeout_seconds=settings.REDIS_LOCK_TIMEOUT_SECONDS
        )
    finally:
        redis_client.close()
        

if __name__ == "__main__":
    main()