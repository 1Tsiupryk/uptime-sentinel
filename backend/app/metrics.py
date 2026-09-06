from typing import Literal

from prometheus_client import Counter, Histogram, Gauge

CheckStatus = Literal["up", "down"]
IncidentEvent = Literal["opened", "resolved"]

CHECKS = Counter(
    "uptime_sentinel_checks",
    "Total number of completed monitor checks", 
    labelnames=("monitor_id", "status")
)

CHECK_LATENCY = Histogram(
    "uptime_sentinel_check_latency_seconds",
    "HTTP monitor check latency in seconds",
    labelnames=("monitor_id",),
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10)
)

INCIDENT_EVENTS = Counter(
    "uptime_sentinel_incident_events",
    "Total number of incident lifecycle events",
    labelnames=("event",)
)

MONITOR_UP = Gauge(
    "uptime_sentinel_monitor_up",
    "Current monitor status based on its latest check",
    labelnames=("monitor_id",),
)

INCIDENT_EVENTS.labels(event="opened")
INCIDENT_EVENTS.labels(event="resolved")

def record_check(monitor_id: int, status: CheckStatus, latency_ms: int) -> None:
    monitor_label = str(monitor_id)

    CHECKS.labels(monitor_id=monitor_label, status=status).inc()
    
    CHECK_LATENCY.labels(monitor_id=monitor_label).observe(max(0, latency_ms) / 1000.0)
    
def record_incident_event(event: IncidentEvent) -> None:
    INCIDENT_EVENTS.labels(event=event).inc()

def set_monitor_statuses(statuses: list[tuple[int, str]]) -> None:
    MONITOR_UP.clear()

    for monitor_id, status in statuses:
        MONITOR_UP.labels(monitor_id=str(monitor_id)).set(1 if status == "up" else 0)
