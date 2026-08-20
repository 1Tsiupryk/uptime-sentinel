from dataclasses import dataclass
from time import perf_counter
from typing import Literal

import httpx

from app.models import Monitor


@dataclass(frozen=True, slots=True)
class CheckOutcome:
    status: Literal["up", "down"]
    status_code: int | None
    latency_ms: int
    error: str | None


def check_monitor(monitor: Monitor) -> CheckOutcome:
    started_at = perf_counter()

    try:
        response = httpx.get(
            monitor.url,
            timeout=monitor.timeout_seconds,
            follow_redirects=False,
        )

        latency_ms = round((perf_counter() - started_at) * 1000)

        if response.status_code == monitor.expected_status_code:
            return CheckOutcome(
                status="up",
                status_code=response.status_code,
                latency_ms=latency_ms,
                error=None,
            )

        return CheckOutcome(
            status="down",
            status_code=response.status_code,
            latency_ms=latency_ms,
            error=(
                f"Expected status {monitor.expected_status_code}, "
                f"received {response.status_code}"
            ),
        )

    except httpx.RequestError as exc:
        latency_ms = round((perf_counter() - started_at) * 1000)

        return CheckOutcome(
            status="down",
            status_code=None,
            latency_ms=latency_ms,
            error=f"{type(exc).__name__}: {exc}",
        )