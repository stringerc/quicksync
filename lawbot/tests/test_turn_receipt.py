"""Turn receipt plain-language summaries."""

import unittest

from lawbot.turn_receipt import build_turn_receipt


class TestTurnReceipt(unittest.TestCase):
    def test_connectivity_short_circuit(self):
        r = build_turn_receipt(
            session_id="s1",
            duration_ms=50,
            out={"answer": "ok"},
            audit={},
            meta_connectivity=True,
        )
        self.assertEqual(r["session_id"], "s1")
        self.assertIn("system check", r["summary_lines"][0].lower())

    def test_skipped_retrieval(self):
        r = build_turn_receipt(
            session_id="s1",
            duration_ms=100,
            out={"retrieval_skipped": True, "answer": "x"},
            audit={"strengthen_always_retrieves": False, "vault_chunk_count": 0},
            meta_connectivity=False,
        )
        self.assertTrue(any("skipped" in x.lower() for x in r["summary_lines"]))

    def test_error_shape(self):
        r = build_turn_receipt(
            session_id="s1",
            duration_ms=10,
            out={"error": "boom"},
            audit={},
            meta_connectivity=False,
        )
        self.assertTrue(any("could not finish" in x.lower() for x in r["summary_lines"]))


if __name__ == "__main__":
    unittest.main()
