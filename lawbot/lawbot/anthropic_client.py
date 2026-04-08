"""
Process-wide ``AsyncAnthropic`` client for Messages API (chat, optional streaming).

Reuses one client per process for HTTP keep-alive. Do not close per request.
Tests may call ``reset_anthropic_client_for_tests``.
"""

from __future__ import annotations

import anthropic

from lawbot.config import settings

_client: anthropic.AsyncAnthropic | None = None


def get_anthropic_async_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    return _client


def reset_anthropic_client_for_tests() -> None:
    global _client
    _client = None
