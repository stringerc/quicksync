"""Transient HTTP retry for OpenAI-compatible chat completions."""

from __future__ import annotations

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
from openai import APIStatusError

from lawbot.config import settings
from lawbot.openai_retry import chat_completions_create_with_retry


def _503() -> APIStatusError:
    req = httpx.Request("POST", "https://example.com/v1/chat/completions")
    resp = httpx.Response(503, request=req)
    return APIStatusError("server busy", response=resp, body=None)


class TestOpenAIRetry(unittest.IsolatedAsyncioTestCase):
    async def test_succeeds_first_call(self):
        ok = MagicMock()
        ok.choices = [MagicMock(message=MagicMock(content="hello"))]
        client = MagicMock()
        client.chat.completions.create = AsyncMock(return_value=ok)
        with patch.object(settings, "lawbot_llm_http_retries", 4):
            out = await chat_completions_create_with_retry(client, model="m", messages=[{"role": "user", "content": "hi"}])
        self.assertEqual(out.choices[0].message.content, "hello")
        self.assertEqual(client.chat.completions.create.await_count, 1)

    async def test_retries_on_503_then_ok(self):
        ok = MagicMock()
        ok.choices = [MagicMock(message=MagicMock(content="ok"))]
        client = MagicMock()
        client.chat.completions.create = AsyncMock(side_effect=[_503(), ok])
        with patch.object(settings, "lawbot_llm_http_retries", 4), patch.object(asyncio, "sleep", new_callable=AsyncMock):
            out = await chat_completions_create_with_retry(client, model="m", messages=[{"role": "user", "content": "x"}])
        self.assertEqual(out.choices[0].message.content, "ok")
        self.assertEqual(client.chat.completions.create.await_count, 2)

    async def test_non_retryable_4xx_raises_immediately(self):
        req = httpx.Request("POST", "https://example.com/v1/chat/completions")
        resp = httpx.Response(400, request=req)
        bad = APIStatusError("bad request", response=resp, body=None)
        client = MagicMock()
        client.chat.completions.create = AsyncMock(side_effect=bad)
        with patch.object(settings, "lawbot_llm_http_retries", 4):
            with self.assertRaises(APIStatusError):
                await chat_completions_create_with_retry(client, model="m", messages=[{"role": "user", "content": "x"}])
        self.assertEqual(client.chat.completions.create.await_count, 1)


if __name__ == "__main__":
    unittest.main()
