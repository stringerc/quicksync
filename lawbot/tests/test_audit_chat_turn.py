"""Integration-style tests for audit mode (mocked LLM and retrieval)."""

import sqlite3
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from lawbot.chat_turn import execute_chat_turn
from lawbot.db import SCHEMA
from lawbot.schemas import ChatIn


class TestAuditChatTurn(unittest.IsolatedAsyncioTestCase):
    async def test_audit_envelope_when_enabled(self):
        conn = sqlite3.connect(":memory:")
        try:
            conn.executescript(SCHEMA)
            app = SimpleNamespace(state=SimpleNamespace(conn=conn, hud_clients=[], hud_last={}))
            req = MagicMock()
            req.app = app

            body = ChatIn(
                message="Review this: Kellos v. Sawilowsky and O.C.G.A. § 9-11-33 in Georgia.",
                session_id="audit-test-session",
                search_case_law=True,
            )

            async def fake_retrieve(conn, q, profile=None):
                return {
                    "chunks": [],
                    "chunk_ids": [],
                    "query_executed": True,
                    "retrieval_failed": False,
                }

            out_chat = {
                "answer": "structured audit reply with enough characters to satisfy the non-empty draft quality check for regression tests.",
                "verification_ok": True,
                "verification_errors": [],
                "model": "mock",
                "session_id": body.session_id,
                "llm_backend": "openai_compatible",
                "retrieval_skipped": False,
                "vault_empty": True,
            }

            with (
                patch("lawbot.chat_turn.retrieve_for_query_conn", side_effect=fake_retrieve),
                patch("lawbot.chat_turn.run_chat", new_callable=AsyncMock, return_value=out_chat),
                patch("lawbot.chat_turn.broadcast_hud", new_callable=AsyncMock),
                patch("lawbot.chat_turn.retrieve_session_context", new_callable=AsyncMock, return_value=([], [])),
                patch("lawbot.chat_turn.ingest_turn", new_callable=AsyncMock),
            ):
                out = await execute_chat_turn(conn, body, req, broadcast=True)

            self.assertIn("audit", out)
            self.assertTrue(out["audit"]["enabled"])
            self.assertEqual(out["audit"].get("mode"), "citation_audit")
            self.assertIsInstance(out["audit"]["extracted_citations"], list)
            self.assertGreater(len(out["audit"]["extracted_citations"]), 0)
            self.assertIn("retrieval_queries_executed", out["audit"])
            self.assertEqual(out["audit"]["vault_chunk_count"], 0)
            self.assertIn("vault_chunk_ids", out["audit"])
            # Several citation-like strings → automatic long-document verification mode.
            self.assertEqual(out["audit"].get("review_pass"), "auto")
            self.assertIsNone(out["audit"].get("task_hint"))
            ds = out.get("draft_shipping")
            self.assertIsInstance(ds, dict)
            self.assertTrue(ds.get("ok"))
            self.assertTrue(ds.get("deterministic_ok"))
            self.assertTrue(ds.get("quote_verification_ok"))
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
