"""
Strict / adversarial API tests: invalid payloads, concurrency, and mocked failure paths.
Does not require a live LLM (uses mocks where chat would otherwise call NVIDIA).
"""

from __future__ import annotations

import asyncio
import unittest
from unittest.mock import patch

import httpx
from asgi_lifespan import LifespanManager
from fastapi.testclient import TestClient

from lawbot.api.app import app

from tests.llm_mock import patched_openai_chat_completion


async def _concurrent_health_status_codes(n: int) -> list[int]:
    """Many parallel GET /health inside one ASGI lifespan (real concurrency, one SQLite handle)."""
    async with LifespanManager(app) as manager:
        transport = httpx.ASGITransport(app=manager.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:

            async def one() -> int:
                r = await client.get("/health")
                return r.status_code

            return await asyncio.gather(*[one() for _ in range(n)])


class TestAPIValidation(unittest.TestCase):
    """Pydantic/FastAPI reject bad input without 500."""

    @classmethod
    def setUpClass(cls):
        cls._tc = TestClient(app)
        cls.client = cls._tc.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls._tc.__exit__(None, None, None)

    def test_malformed_json_422(self):
        r = self.client.post(
            "/v1/chat",
            content="not json {",
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(r.status_code, 422)

    def test_missing_message_422(self):
        r = self.client.post("/v1/chat", json={})
        self.assertEqual(r.status_code, 422)
        self.assertIn("message", r.text.lower())

    def test_wrong_message_type_422(self):
        r = self.client.post("/v1/chat", json={"message": 12345})
        self.assertEqual(r.status_code, 422)

    def test_health_ok(self):
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json().get("status"), "ok")


class TestHermesAdversarial(unittest.TestCase):
    """Hermes endpoint must never 500 on garbage JSON shapes."""

    @classmethod
    def setUpClass(cls):
        cls._tc = TestClient(app)
        cls.client = cls._tc.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls._tc.__exit__(None, None, None)

    def test_non_string_answer_returns_200_with_schema_error(self):
        r = self.client.post(
            "/v1/hermes/check",
            json={
                "answer": ["not", "a", "string"],
                "verification_ok": True,
                "verification_errors": [],
                "vault_empty": True,
                "session_id": "x",
            },
        )
        self.assertEqual(r.status_code, 200, r.text)
        j = r.json()
        self.assertFalse(j.get("hermes_passed"))
        self.assertTrue(any("string" in e.lower() for e in (j.get("errors") or [])))

    def test_large_answer_string_survives(self):
        big = "word " * 15_000
        r = self.client.post(
            "/v1/hermes/check",
            json={
                "answer": big,
                "verification_ok": True,
                "verification_errors": [],
                "vault_empty": True,
                "session_id": "stress",
            },
        )
        self.assertEqual(r.status_code, 200, r.text[:500])
        j = r.json()
        self.assertIn("hermes_passed", j)


class TestConcurrentHealth(unittest.TestCase):
    """Concurrent /health requests with LifespanManager + httpx.AsyncClient (not parallel TestClients)."""

    def test_concurrent_health_checks_single_lifespan(self):
        n = 48
        codes = asyncio.run(_concurrent_health_status_codes(n))
        self.assertEqual(len(codes), n)
        self.assertTrue(all(c == 200 for c in codes), codes)


class TestStreamFailurePath(unittest.TestCase):
    """SSE stream reports error when the worker raises instead of hanging."""

    @classmethod
    def setUpClass(cls):
        cls._tc = TestClient(app)
        cls.client = cls._tc.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls._tc.__exit__(None, None, None)

    def test_stream_emits_error_event_when_execute_raises(self):
        async def boom(*_a, **_kw):
            raise RuntimeError("injected fault for resilience test")

        with patch("lawbot.api.app.execute_chat_turn", new=boom):
            with self.client.stream(
                "POST",
                "/v1/chat/stream",
                json={
                    "message": "hello",
                    "session_id": None,
                    "search_case_law": False,
                },
            ) as r:
                self.assertEqual(r.status_code, 200)
                body = "".join(r.iter_text())
        self.assertIn("error", body)
        self.assertIn("injected fault", body)


class TestChatWithMockedLLM(unittest.TestCase):
    """End-to-end chat survives when OpenAI client is mocked (no network)."""

    @classmethod
    def setUpClass(cls):
        cls._tc = TestClient(app)
        cls.client = cls._tc.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls._tc.__exit__(None, None, None)

    def test_chat_ok_with_mock_completion(self):
        with patched_openai_chat_completion("OK from mock."):
            r = self.client.post(
                "/v1/chat",
                json={
                    "message": "Resilience ping",
                    "session_id": "resilience-mock-session",
                    "search_case_law": False,
                },
            )
        self.assertEqual(r.status_code, 200, r.text[:500])
        j = r.json()
        self.assertIn("answer", j)
        self.assertIn("turn_receipt", j)
        self.assertIn("summary_lines", j["turn_receipt"])

    def test_large_user_message_does_not_500(self):
        """Long prompts should return a normal JSON shape or 4xx — never an unhandled 500."""
        body = "word " * 12_000
        with patched_openai_chat_completion("ack"):
            r = self.client.post(
                "/v1/chat",
                json={
                    "message": body,
                    "session_id": None,
                    "search_case_law": False,
                },
            )
        self.assertNotEqual(r.status_code, 500, r.text[:500])
        if r.status_code == 200:
            j = r.json()
            self.assertTrue("answer" in j or "error" in j, j)


if __name__ == "__main__":
    unittest.main()
