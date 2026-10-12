"""Small in-memory metrics collector; suitable for local experiments, not persistence."""

from __future__ import annotations

from collections import Counter
from threading import Lock
from typing import Any


class Metrics:
    def __init__(self) -> None:
        self._lock = Lock()
        self._requests = 0
        self._status_codes: Counter[str] = Counter()
        self._faults: Counter[str] = Counter()
        self._durations_ms: list[float] = []

    def record(self, *, status_code: int, fault: str, duration_ms: float) -> None:
        with self._lock:
            self._requests += 1
            self._status_codes[str(status_code)] += 1
            if fault != "none":
                self._faults[fault] += 1
            self._durations_ms.append(round(duration_ms, 3))

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            durations = sorted(self._durations_ms)
            return {
                "requests_total": self._requests,
                "responses_by_status": dict(self._status_codes),
                "injected_faults": dict(self._faults),
                "latency_ms": {
                    "count": len(durations),
                    "mean": round(sum(durations) / len(durations), 3) if durations else 0,
                    "p50": _percentile(durations, 0.50),
                    "p95": _percentile(durations, 0.95),
                },
                "note": "In-memory metrics reset when the process restarts; not intended for production monitoring.",
            }


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0
    index = max(0, min(len(values) - 1, int((len(values) - 1) * percentile)))
    return values[index]
