from unittest.mock import Mock

from app.services.monitor_lock import try_acquire_monitor_lock

def test_acquire_monitor_lock_returns_lock() -> None:
    client = Mock()
    lock = Mock()
    lock.acquire.return_value = True
    client.lock.return_value = lock

    result = try_acquire_monitor_lock(
        client=client,
        monitor_id=42,
        timeout_seconds=90,
    )

    assert result is lock

    client.lock.assert_called_once_with(
        name="uptime-sentinel:monitor-check:42",
        timeout=90,
    )
    lock.acquire.assert_called_once_with(blocking=False)

def test_acquire_monitor_lock_returns_none_when_busy() -> None:
    client = Mock()
    lock = Mock()
    lock.acquire.return_value = False
    client.lock.return_value = lock

    result = try_acquire_monitor_lock(
        client=client,
        monitor_id=42,
        timeout_seconds=90,
    )

    assert result is None
    lock.acquire.assert_called_once_with(blocking=False)