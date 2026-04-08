"""
End-to-end HTTP test: mock the OpenAI-compatible client so the model "returns" toxic junk;
assert the server still strips hallucinated cites (full path: execute_chat_turn → run_chat → _finalize_answer).

This is what "verified" means here — not trusting unit tests of helpers alone, and not requiring a live LLM.
"""

from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from lawbot.api.app import app
from lawbot.config import settings as lawbot_settings


# Simulated worst-case model output (patterns from real bad runs).
_TOXIC_LLM = """
Based on the provided SOURCE CHUNKS, I'll verify without relying on the allowed chunk IDs.
To serve as a top 0.01% attorney:

1. O.C.G.A. § 9-3-25 — malpractice limitations.
2. Kellos v. Sawilowsky, 254 Ga. 4 — standard of care.

Here are the verified cases and laws:
1. O.C.G.A. § 15-10-45(d)
2. Cox-Ott v. Barnes, 2025 Ga. LEXIS 98

To confirm verified cases and laws:
1. O.C.G.A. § 9-11-33
"""


def _fake_completion(content: str) -> MagicMock:
    return MagicMock(choices=[MagicMock(message=MagicMock(content=content))])


class TestE2EMockLLMSanitize(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tc = TestClient(app)
        cls.client = cls._tc.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls._tc.__exit__(None, None, None)

    def _post_with_mock_openai(self, payload: dict) -> dict:
        async def fake_create(**_kwargs):
            return _fake_completion(_TOXIC_LLM)

        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=fake_create)

        with patch("lawbot.chat_service.get_openai_compatible_client", return_value=mock_client):
            with patch.object(lawbot_settings, "nvidia_api_key", "sk-mock-e2e"):
                with patch.object(lawbot_settings, "anthropic_api_key", ""):
                    with patch.object(lawbot_settings, "lawbot_embedding_model", ""):
                        r = self.client.post("/v1/chat", json=payload)
        self.assertEqual(r.status_code, 200, r.text[:800])
        return r.json()

    def test_conversational_empty_vault_strips_toxic_mock(self):
        """Short question, no cites in user text → conversational sanitize."""
        j = self._post_with_mock_openai(
            {
                "message": "Say hello in five words.",
                "session_id": None,
                "search_case_law": False,
            }
        )
        self.assertNotIn("error", j or {})
        ans = (j.get("answer") or "").lower()
        self.assertNotIn("o.c.g.a.", ans)
        self.assertNotIn("kellos", ans)
        self.assertNotIn("top 0.01", ans)
        self.assertNotIn("source chunks", ans)
        self.assertTrue(j.get("vault_empty") is True)

    def test_audit_empty_vault_strips_toxic_mock(self):
        """User message contains O.C.G.A. → citation audit mode → audit sanitize."""
        j = self._post_with_mock_openai(
            {
                "message": "Under O.C.G.A. § 9-3-25, what is the limitations period for malpractice?",
                "session_id": None,
                "search_case_law": False,
            }
        )
        self.assertNotIn("error", j or {})
        ans = j.get("answer") or ""
        self.assertNotIn("O.C.G.A. § 9-11-33", ans)  # line from toxic tail
        self.assertNotIn("Kellos", ans)
        self.assertNotIn("top 0.01", ans.lower())
        self.assertNotIn("SOURCE CHUNKS", ans)
        self.assertIn("Sources in vault", ans)  # audit header preserved / ensured
        self.assertTrue(j.get("vault_empty") is True)


if __name__ == "__main__":
    unittest.main()
