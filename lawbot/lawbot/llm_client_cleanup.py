"""Close OpenAI/Anthropic async SDK clients; safe when tests pass MagicMocks."""

from __future__ import annotations

import asyncio
from typing import Any


async def aclose_if_real(client: Any) -> None:
    """Call await client.close() only if it returns a coroutine (skips unittest mocks)."""
    close = getattr(client, "close", None)
    if not callable(close):
        return
    res = close()
    if asyncio.iscoroutine(res):
        await res
