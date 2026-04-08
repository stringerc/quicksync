"""Phase 8 — simple per-IP fixed-window rate limit for chat endpoints (0 = disabled)."""

from __future__ import annotations

import time
from typing import Any

from starlette.requests import Request
from starlette.responses import JSONResponse


class ChatRateLimiter:
    """Fixed 60s windows per IP: key -> (window_epoch_minute, count)."""

    def __init__(self) -> None:
        self._data: dict[str, tuple[int, int]] = {}

    def allow(self, client_ip: str, per_minute: int) -> bool:
        if per_minute <= 0:
            return True
        bucket = int(time.time() // 60)
        key = client_ip or "unknown"
        w, c = self._data.get(key, (bucket, 0))
        if w != bucket:
            w, c = bucket, 0
        c += 1
        self._data[key] = (w, c)
        if len(self._data) > 50_000:
            self._data = {k: v for k, v in self._data.items() if v[0] >= bucket - 2}
        return c <= per_minute


def register_rate_limit_middleware(app: Any, get_per_minute: Any) -> None:
    """``get_per_minute`` is a zero-arg callable returning current cap (e.g. ``settings`` field)."""
    limiter = ChatRateLimiter()

    @app.middleware("http")
    async def _rate_limit(request: Request, call_next):  # type: ignore[misc]
        cap = int(get_per_minute() or 0)
        path = request.url.path
        if cap <= 0 or path not in ("/v1/chat", "/v1/chat/stream"):
            return await call_next(request)
        ip = request.client.host if request.client else "unknown"
        if limiter.allow(ip, cap):
            return await call_next(request)
        return JSONResponse(
            {"error": "rate_limited", "detail": "Too many requests — try again shortly."},
            status_code=429,
        )
