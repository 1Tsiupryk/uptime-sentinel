from redis import Redis
from redis.lock import Lock

def try_acquire_monitor_lock(
    client: Redis,
    monitor_id: int,
    timeout_seconds: int,
) -> Lock | None:
    lock = client.lock(
        name=f"uptime-sentinel:monitor-check:{monitor_id}", 
        timeout=timeout_seconds
    )

    if not lock.acquire(blocking=False):
        return None

    return lock