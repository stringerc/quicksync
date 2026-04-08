"""turn_signals regime + Hermes packaging."""

import unittest

from lawbot.turn_signals import build_turn_signals, classify_task_regime


class TestTurnSignals(unittest.TestCase):
    def test_regime_connectivity(self):
        r = classify_task_regime(
            meta_connectivity=True,
            use_citation_audit=False,
            document_mode=True,
            task_hint=None,
            message_len=100,
        )
        self.assertEqual(r, "connectivity")

    def test_regime_conversational(self):
        r = classify_task_regime(
            meta_connectivity=False,
            use_citation_audit=False,
            document_mode=False,
            task_hint=None,
            message_len=50,
        )
        self.assertEqual(r, "conversational")

    def test_build_turn_signals_minimal(self):
        out = {
            "answer": "ok",
            "verification_ok": True,
            "verification_errors": [],
            "vault_empty": True,
            "session_id": "s",
            "audit": {"vault_chunk_ids": []},
            "draft_shipping": {"needs_confirmation": False},
            "draft_quality": {"score_percent": 90},
        }
        ts = build_turn_signals(
            None,
            out,
            body_message="hello",
            meta_connectivity=False,
            use_citation_audit=False,
            document_mode=False,
            task_hint=None,
            chunk_ids=[],
            queries_ran=[],
        )
        self.assertIn("task_regime", ts)
        self.assertIn("gates", ts)
        self.assertIn("hermes", ts)
        self.assertEqual(ts["retrieval_depth"]["queries_executed"], 0)
        self.assertEqual(ts["answer_depth"]["level"], "standard")

    def test_retrieval_depth_coherence(self):
        out = {
            "answer": "ok",
            "verification_ok": True,
            "verification_errors": [],
            "vault_empty": True,
            "session_id": "s",
            "audit": {"vault_chunk_ids": []},
            "draft_shipping": {"needs_confirmation": False},
            "draft_quality": {"score_percent": 90},
        }
        ts = build_turn_signals(
            None,
            out,
            body_message="hello",
            meta_connectivity=False,
            use_citation_audit=False,
            document_mode=False,
            task_hint=None,
            chunk_ids=[],
            queries_ran=["a", "b"],
            retrieval_coherence=0.33,
            retrieval_coherence_trimmed=True,
        )
        self.assertEqual(ts["retrieval_depth"]["queries_executed"], 2)
        self.assertEqual(ts["retrieval_depth"]["coherence_score"], 0.33)
        self.assertTrue(ts["retrieval_depth"]["coherence_trimmed"])


if __name__ == "__main__":
    unittest.main()
