"""
Process-wide AsyncOpenAI client for OpenAI-compatible endpoints (chat, embeddings elsewhere).

Reuses one client per process to benefit from HTTP keep-alive and connection pooling.
Do not close per request; tests may call ``reset_openai_compatible_client_for_tests``.
"""

from __future__ import annotations

from openai import AsyncOpenAI

from lawbot.config import settings

_client: AsyncOpenAI | None = None


def get_openai_compatible_client() -> AsyncOpenAI:
    """Lazy singleton; same base URL + key for the lifetime of the process."""
    global _client
    if _client is None:
        key = settings.openai_compatible_key()
        _client = AsyncOpenAI(base_url=settings.openai_base_url, api_key=key)
    return _client


def reset_openai_compatible_client_for_tests() -> None:
    """Unit tests only: drop cached client so patched factories take effect."""
    global _client
    _client = None
