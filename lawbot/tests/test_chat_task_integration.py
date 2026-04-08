"""
HTTP-level checks for task routing (verify / strengthen) with LLM + retrieval mocked.
"""

from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from lawbot.api.app import app
from lawbot.intent import CHAT_TASK_STRENGTHEN_FILING, CHAT_TASK_VERIFY_CITATIONS


class TestChatTaskIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tc = TestClient(app)
        cls.client = cls._tc.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls._tc.__exit__(None, None, None)

    @staticmethod
    def _empty_retrieval():
        return {
            "chunks": [],
            "chunk_ids": [],
            "query_executed": True,
            "retrieval_failed": False,
            "retrieval_skipped": False,
        }

    @staticmethod
    def _stub_run_chat_out():
        return {
            "answer": "stubbed assistant reply for test",
            "verification_ok": True,
            "verification_errors": [],
            "model": "mock",
            "session_id": "ignored",
            "llm_backend": "openai_compatible",
            "retrieval_skipped": False,
            "vault_empty": True,
        }

    @patch("lawbot.chat_turn.ingest_turn", new_callable=AsyncMock)
    @patch("lawbot.chat_turn.retrieve_session_context", new_callable=AsyncMock)
    @patch("lawbot.chat_turn.run_chat", new_callable=AsyncMock)
    @patch("lawbot.chat_turn.retrieve_for_query_conn", new_callable=AsyncMock)
    def test_post_chat_sets_verify_task_hint(self, mock_retrieve, mock_run_chat, mock_session_rag, _mock_ingest):
        mock_retrieve.side_effect = lambda *a, **k: self._empty_retrieval()
        mock_run_chat.return_value = self._stub_run_chat_out()
        mock_session_rag.return_value = ([], [])

        r = self.client.post(
            "/v1/chat",
            json={
                "message": (
                    "Please verify the cases and laws in this list: "
                    "Smith v. Jones, 123 Ga. App. 1, and O.C.G.A. § 9-11-33."
                ),
                "session_id": None,
                "search_case_law": True,
            },
        )
        self.assertEqual(r.status_code, 200, r.text[:500])
        j = r.json()
        self.assertEqual(j.get("audit", {}).get("task_hint"), CHAT_TASK_VERIFY_CITATIONS)
        self.assertTrue(j.get("audit", {}).get("enabled"))
        mock_run_chat.assert_awaited()

    @patch("lawbot.chat_turn.ingest_turn", new_callable=AsyncMock)
    @patch("lawbot.chat_turn.retrieve_session_context", new_callable=AsyncMock)
    @patch("lawbot.chat_turn.run_chat", new_callable=AsyncMock)
    @patch("lawbot.chat_turn.retrieve_for_query_conn", new_callable=AsyncMock)
    def test_verify_forces_chat_output_when_document_mode_requested(
        self, mock_retrieve, mock_run_chat, mock_session_rag, _mock_ingest
    ):
        """UI defaults to document; verification must stay a cite matrix, not a full pleading rewrite."""
        mock_retrieve.side_effect = lambda *a, **k: self._empty_retrieval()
        mock_run_chat.return_value = self._stub_run_chat_out()
        mock_session_rag.return_value = ([], [])

        r = self.client.post(
            "/v1/chat",
            json={
                "message": (
                    "Please verify the cases and laws in this list: "
                    "Smith v. Jones, 123 Ga. App. 1, and O.C.G.A. § 9-11-33."
                ),
                "session_id": None,
                "search_case_law": True,
                "response_mode": "document",
            },
        )
        self.assertEqual(r.status_code, 200, r.text[:500])
        j = r.json()
        self.assertEqual(j.get("audit", {}).get("task_hint"), CHAT_TASK_VERIFY_CITATIONS)
        self.assertTrue(j.get("audit", {}).get("document_mode_requested"))
        self.assertFalse(j.get("audit", {}).get("document_mode_effective"))
        primary = [
            c
            for c in mock_run_chat.await_args_list
            if c.kwargs.get("timing_segment") == "primary"
        ]
        self.assertEqual(len(primary), 1, "expected exactly one primary LLM call")
        self.assertFalse(primary[0].kwargs.get("document_mode"))

    @patch("lawbot.chat_turn.ingest_turn", new_callable=AsyncMock)
    @patch("lawbot.chat_turn.retrieve_session_context", new_callable=AsyncMock)
    @patch("lawbot.chat_turn.run_chat", new_callable=AsyncMock)
    @patch("lawbot.chat_turn.retrieve_for_query_conn", new_callable=AsyncMock)
    def test_post_chat_sets_strengthen_task_hint(self, mock_retrieve, mock_run_chat, mock_session_rag, _mock_ingest):
        mock_retrieve.side_effect = lambda *a, **k: self._empty_retrieval()
        mock_run_chat.return_value = self._stub_run_chat_out()
        mock_session_rag.return_value = ([], [])

        r = self.client.post(
            "/v1/chat",
            json={
                "message": "How can I strengthen this motion to dismiss under Georgia law?",
                "session_id": None,
                "search_case_law": True,
            },
        )
        self.assertEqual(r.status_code, 200, r.text[:500])
        j = r.json()
        self.assertEqual(j.get("audit", {}).get("task_hint"), CHAT_TASK_STRENGTHEN_FILING)
        self.assertFalse(j.get("audit", {}).get("enabled"))

    @patch("lawbot.chat_turn.ingest_turn", new_callable=AsyncMock)
    @patch("lawbot.chat_turn.retrieve_session_context", new_callable=AsyncMock)
    @patch("lawbot.chat_turn.run_chat", new_callable=AsyncMock)
    @patch("lawbot.chat_turn.retrieve_for_query_conn", new_callable=AsyncMock)
    def test_long_strengthen_runs_courtlistener_even_if_paste_only_requested(self, mock_retrieve, mock_run_chat, mock_session_rag, _mock_ingest):
        """Strengthen-this-filing always retrieves when search_case_law is on (paste-only is ignored)."""
        mock_retrieve.side_effect = lambda *a, **k: self._empty_retrieval()
        mock_run_chat.return_value = self._stub_run_chat_out()
        mock_session_rag.return_value = ([], [])
        msg = (
            "can we make sure that this is written in a way a top .01% appellate attorney would write it:\n\n"
            "IN THE MAGISTRATE COURT\nCOMES NOW Defendant.\n\n"
            + ("paragraph text. " * 400)
        )
        r = self.client.post(
            "/v1/chat",
            json={
                "message": msg,
                "session_id": None,
                "search_case_law": True,
                "paste_only_no_research": True,
            },
        )
        self.assertEqual(r.status_code, 200, r.text[:500])
        self.assertGreaterEqual(mock_retrieve.await_count, 1)
        j = r.json()
        self.assertEqual(j.get("audit", {}).get("task_hint"), CHAT_TASK_STRENGTHEN_FILING)
        self.assertTrue(j.get("audit", {}).get("strengthen_always_retrieves"))
        self.assertFalse(j.get("audit", {}).get("paste_only_no_research_effective"))
        self.assertFalse(j.get("audit", {}).get("enabled"))

    @patch("lawbot.chat_turn.ingest_turn", new_callable=AsyncMock)
    @patch("lawbot.chat_turn.retrieve_session_context", new_callable=AsyncMock)
    @patch("lawbot.chat_turn.run_chat", new_callable=AsyncMock)
    @patch("lawbot.chat_turn.retrieve_for_query_conn", new_callable=AsyncMock)
    def test_long_strengthen_document_mode_calls_retrieve_by_default(self, mock_retrieve, mock_run_chat, mock_session_rag, _mock_ingest):
        mock_retrieve.side_effect = lambda *a, **k: self._empty_retrieval()
        mock_run_chat.return_value = self._stub_run_chat_out()
        mock_session_rag.return_value = ([], [])
        msg = (
            "strengthen this filing for Georgia magistrate\n\n"
            "IN THE MAGISTRATE COURT OF GWINNETT COUNTY\nANSWER\n\n"
            + ("paragraph text. " * 400)
        )
        r = self.client.post(
            "/v1/chat",
            json={
                "message": msg,
                "session_id": None,
                "search_case_law": True,
                "response_mode": "document",
                "two_phase_filing": False,
            },
        )
        self.assertEqual(r.status_code, 200, r.text[:500])
        self.assertGreaterEqual(mock_retrieve.await_count, 1)
        j = r.json()
        self.assertEqual(j.get("audit", {}).get("task_hint"), CHAT_TASK_STRENGTHEN_FILING)


if __name__ == "__main__":
    unittest.main()
