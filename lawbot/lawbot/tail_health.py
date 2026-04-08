"""
Process-local tail-health metrics for LLM backends (Resonance-style routing signals).

Tracks rolling latencies and recent HTTP 429s for observability on ``llm_complete`` / ``turn_decision``.
Thread-safe for async FastAPI workers.
"""

from __future__ import annotations

import threading
import time
from collections import deque
from typing import Any

# Rolling window for rate-limit events (seconds).
_RATE_WINDOW_S = 3600.0
# Samples kept per backend for median latency (last N completion durations).
_LATENCY_MAX = 20

_lock = threading.Lock()
# backend -> deque of duration_ms (most recent last)
_latencies: dict[str, deque[float]] = {}
# backend -> monotonic timestamp of last 429
_last_429_mono: dict[str, float] = {}
# backend -> deque of wall-time timestamps (time.time()) for 429s in window
_429_events: dict[str, deque[float]] = {}


def _backend_key(backend: str) -> str:
    b = (backend or "").strip().lower()
    return b if b else "unknown"


def record_latency_ms(backend: str, duration_ms: float) -> None:
    """Record a successful LLM call duration (wall-clock ms)."""
    if duration_ms < 0 or duration_ms > 1e7:
        return
    key = _backend_key(backend)
    with _lock:
        d = _latencies.setdefault(key, deque(maxlen=_LATENCY_MAX))
        d.append(float(duration_ms))


def record_http_429(backend: str) -> None:
    """Record an HTTP 429 (rate limit) from the provider API."""
    key = _backend_key(backend)
    now = time.time()
    mono = time.monotonic()
    with _lock:
        _last_429_mono[key] = mono
        ev = _429_events.setdefault(key, deque())
        ev.append(now)
        _prune_events(ev, now)


def _prune_events(ev: deque[float], now: float) -> None:
    while ev and now - ev[0] > _RATE_WINDOW_S:
        ev.popleft()


def _median_last_n(values: list[float], n: int) -> float | None:
    if not values:
        return None
    chunk = values[-n:]
    s = sorted(chunk)
    m = len(s) // 2
    if len(s) % 2:
        return float(s[m])
    return float((s[m - 1] + s[m]) / 2.0)


def snapshot_for_backend(backend: str) -> dict[str, Any]:
    """JSON-safe fields for a single backend (e.g. the one used for this ``llm_complete``)."""
    key = _backend_key(backend)
    now = time.time()
    with _lock:
        lat = list(_latencies.get(key, deque()))
        ev = _429_events.get(key)
        ev_list = list(ev) if ev else []
        last429_mono = _last_429_mono.get(key)

    med_10 = _median_last_n(lat, 10)
    med_20 = _median_last_n(lat, 20)
    sec_since_429: float | None = None
    if last429_mono is not None:
        sec_since_429 = round(time.monotonic() - last429_mono, 2)

    rl_1h = sum(1 for t in ev_list if now - t <= _RATE_WINDOW_S)

    return {
        "tail_median_latency_ms_10": round(med_10, 2) if med_10 is not None else None,
        "tail_median_latency_ms_20": round(med_20, 2) if med_20 is not None else None,
        "tail_latency_samples": len(lat),
        "tail_rate_limit_events_1h": rl_1h,
        "tail_sec_since_429": sec_since_429,
    }


def snapshot_all_backends() -> dict[str, Any]:
    """Compact multi-backend snapshot for ``turn_decision`` (process-wide)."""
    keys = {"openai_compatible", "anthropic"}
    out: dict[str, Any] = {}
    for k in sorted(keys):
        snap = snapshot_for_backend(k)
        prefix = "oc" if k == "openai_compatible" else "anth"
        for field, val in snap.items():
            short = field.replace("tail_", "")
            out[f"tail_{prefix}_{short}"] = val
    return out


def reset_tail_health_for_tests() -> None:
    """Unit tests only."""
    with _lock:
        _latencies.clear()
        _last_429_mono.clear()
        _429_events.clear()
