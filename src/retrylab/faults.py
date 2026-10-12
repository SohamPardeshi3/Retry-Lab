"""Deterministic fault scenarios used by the RetryLab proxy."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Literal

FaultKind = Literal["none", "latency", "server_error", "rate_limit", "timeout"]


@dataclass(frozen=True, slots=True)
class FaultScenario:
    """A validated, per-request fault instruction."""

    kind: FaultKind = "none"
    delay_ms: int = 0
    status_code: int = 503
    retry_after_seconds: int = 1

    @classmethod
    def from_header(cls, value: str | None) -> "FaultScenario":
        """Parse a safe, intentionally small scenario vocabulary from a request header.

        Accepted forms: ``latency:250``, ``server_error:503``, ``rate_limit`` and
        ``timeout:1500``. Timeout means delaying before returning a simulated 504; it
        does not abort the proxy's own upstream connection.
        """
        if not value:
            return cls()
        raw = value.strip().lower()
        if raw == "rate_limit":
            return cls(kind="rate_limit", status_code=429)
        if raw.startswith("latency:"):
            delay = _parse_bounded_int(raw.partition(":")[2], minimum=1, maximum=10_000)
            return cls(kind="latency", delay_ms=delay)
        if raw.startswith("timeout:"):
            delay = _parse_bounded_int(raw.partition(":")[2], minimum=1, maximum=30_000)
            return cls(kind="timeout", delay_ms=delay, status_code=504)
        if raw.startswith("server_error:"):
            status = _parse_bounded_int(raw.partition(":")[2], minimum=500, maximum=599)
            return cls(kind="server_error", status_code=status)
        raise ValueError("Unsupported X-RetryLab-Fault value")

    async def before_upstream(self) -> None:
        """Apply latency faults before contacting the upstream service."""
        if self.kind == "latency":
            await asyncio.sleep(self.delay_ms / 1000)


def _parse_bounded_int(value: str, *, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("Fault parameter must be an integer") from exc
    if not minimum <= parsed <= maximum:
        raise ValueError(f"Fault parameter must be between {minimum} and {maximum}")
    return parsed
