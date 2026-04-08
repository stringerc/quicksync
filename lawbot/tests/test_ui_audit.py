"""
Automated UI / static asset audit for Lawbot.
Run: cd lawbot && python -m pytest tests/test_ui_audit.py -v
   or: python -m unittest tests.test_ui_audit -v
"""

from __future__ import annotations

import re
import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from lawbot.api.app import STATIC_DIR, app

from tests.llm_mock import patched_openai_chat_completion


class LawbotUIAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Lifespan must run so app.state.conn exists for /v1/chat
        cls._tc = TestClient(app)
        cls.client = cls._tc.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls._tc.__exit__(None, None, None)

    def test_get_root_returns_html(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertIn("text/html", r.headers.get("content-type", ""))
        body = r.text
        self.assertIn("Lawbot", body)
        self.assertIn('id="sendBtn"', body)
        self.assertIn('id="newSessionBtn"', body)
        self.assertIn('id="message"', body)
        self.assertIn('id="researchQuery"', body)
        self.assertIn('id="sessionSelect"', body)
        self.assertIn('id="documentModeToggle"', body)
        self.assertIn('src="/static/app.js"', body)
        self.assertIn('href="/static/styles.css"', body)

    def test_static_assets_exist_and_served(self):
        for path in (
            "/static/styles.css",
            "/static/app.js",
            "/static/favicon.svg",
            "/static/trust.html",
        ):
            with self.subTest(path=path):
                r = self.client.get(path)
                self.assertEqual(r.status_code, 200, f"{path} must return 200")
                self.assertGreater(len(r.content), 10)

    def test_favicon_ico(self):
        r = self.client.get("/favicon.ico")
        self.assertEqual(r.status_code, 200)
        self.assertIn("image", r.headers.get("content-type", ""))

    def test_health_json(self):
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200)
        j = r.json()
        self.assertEqual(j.get("status"), "ok")
        self.assertIn("llm_backend", j)

    def test_openapi_docs_available(self):
        r = self.client.get("/docs")
        self.assertEqual(r.status_code, 200)
        self.assertIn("swagger", r.text.lower())

    def test_app_js_references_valid_dom_ids(self):
        """Ensure every #id used in app.js exists in index.html."""
        html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
        js = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
        ids = set(re.findall(r'\$\("#([^"]+)"\)', js))
        for i in ids:
            with self.subTest(id=i):
                self.assertIn(f'id="{i}"', html, f"Missing element #{i} for app.js")

    def test_sessions_list_routes(self):
        r = self.client.get("/v1/sessions")
        self.assertEqual(r.status_code, 200)
        self.assertIn("sessions", r.json())

    def test_chat_stream_returns_sse_steps_and_complete(self):
        """SSE stream should emit at least one step and a final complete payload."""
        with patched_openai_chat_completion("streamok"):
            with self.client.stream(
                "POST",
                "/v1/chat/stream",
                json={
                    "message": "Reply with exactly one word: streamok",
                    "session_id": None,
                    "search_case_law": False,
                },
            ) as r:
                self.assertEqual(r.status_code, 200)
                raw = r.read()
        text = raw.decode("utf-8", errors="replace")
        self.assertIn('"event": "step"', text)
        self.assertIn('"event": "token"', text)
        self.assertIn('"event": "complete"', text)
        self.assertIn('"answer"', text)

    def test_chat_endpoint_accepts_minimal_payload(self):
        """Smoke: POST /v1/chat returns JSON with answer or error."""
        with patched_openai_chat_completion("pong"):
            with patch(
                "lawbot.providers.courtlistener.search_opinions",
                new=AsyncMock(return_value=[]),
            ):
                r = self.client.post(
                    "/v1/chat",
                    json={"message": "ping", "session_id": None, "research_query": "test"},
                )
        self.assertEqual(r.status_code, 200, r.text[:500])
        j = r.json()
        self.assertTrue("answer" in j or "error" in j, j)


if __name__ == "__main__":
    unittest.main()
