"""
Retry transient OpenAI-compatible HTTP failures (rate limits, 5xx, connection drops).

Used for chat completions, embeddings (session RAG), and auxiliary calls.

Configurable via ``LAWBOT_LLM_HTTP_RETRIES`` (minimum 1 attempt; default 4; set ``1`` to disable backoff retries).
"""

from __future__ import annotations

import asyncio
import random
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from openai import (
    APIConnectionError,
    APIStatusError,
    AsyncOpenAI,
    APITimeoutError,
    RateLimitError,
)

from lawbot.config import settings
from lawbot.tail_health import record_http_429

T = TypeVar("T")

# Transient server / gateway codes worth backoff retries.
_RETRYABLE_STATUS = frozenset({408, 429, 500, 502, 503, 504})


def _max_attempts() -> int:
    n = int(getattr(settings, "lawbot_llm_http_retries", 4) or 1)
    return max(1, min(n, 8))


async def _retry_openai_call(coro_factory: Callable[[], Awaitable[T]]) -> T:
    attempts = _max_attempts()
    last_exc: Exception | None = None
    for attempt in range(attempts):
        try:
            return await coro_factory()
        except RateLimitError as e:
            last_exc = e
            record_http_429("openai_compatible")
        except APIConnectionError as e:
            last_exc = e
        except APITimeoutError as e:
            last_exc = e
        except APIStatusError as e:
            if e.status_code not in _RETRYABLE_STATUS:
                raise
            last_exc = e
            if e.status_code == 429:
                record_http_429("openai_compatible")
        if attempt == attempts - 1:
            assert last_exc is not None
            raise last_exc
        base = 0.75 * (2**attempt)
        jitter = random.uniform(0.05, 0.4)
        await asyncio.sleep(min(base + jitter, 30.0))


async def chat_completions_create_with_retry(
    client: AsyncOpenAI,
    **create_kw: Any,
) -> Any:
    """Call ``client.chat.completions.create`` with exponential backoff on transient errors."""

    async def _call() -> Any:
        return await client.chat.completions.create(**create_kw)

    return await _retry_openai_call(_call)


async def chat_completions_stream_create_with_retry(
    client: AsyncOpenAI,
    **create_kw: Any,
) -> Any:
    """
    Open a streaming chat completion (``stream=True``) with the same retry policy on *connection*.

    Mid-stream failures are not retried (caller would need a fresh request).
    """

    merged = dict(create_kw)
    merged["stream"] = True

    async def _call() -> Any:
        return await client.chat.completions.create(**merged)

    return await _retry_openai_call(_call)


async def embeddings_create_with_retry(
    client: AsyncOpenAI,
    **embed_kw: Any,
) -> Any:
    """Call ``client.embeddings.create`` with the same backoff policy (session RAG)."""

    async def _call() -> Any:
        return await client.embeddings.create(**embed_kw)

    return await _retry_openai_call(_call)
