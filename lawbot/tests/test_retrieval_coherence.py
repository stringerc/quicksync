"""Retrieval coherence heuristic."""

import unittest

from lawbot.retrieval_coherence import (
    apply_coherence_query_cap,
    coherence_score_for_retrieval,
)


class TestRetrievalCoherence(unittest.TestCase):
    def test_short_message_low_score(self):
        s = coherence_score_for_retrieval("hi", document_mode=False, explicit_research_query=None)
        self.assertLess(s, 0.3)

    def test_explicit_query_high(self):
        s = coherence_score_for_retrieval(
            "x",
            document_mode=False,
            explicit_research_query="negligence standard",
        )
        self.assertGreaterEqual(s, 0.8)

    def test_trim_multi_query(self):
        qs = ["q1", "q2", "q3"]
        out, trimmed = apply_coherence_query_cap(
            qs,
            coherence=0.2,
            include_authority_pack=False,
            force_authority=False,
        )
        self.assertTrue(trimmed)
        self.assertEqual(out, ["q1"])

    def test_no_trim_authority_pack(self):
        qs = ["q1", "q2"]
        out, trimmed = apply_coherence_query_cap(
            qs,
            coherence=0.2,
            include_authority_pack=True,
            force_authority=False,
        )
        self.assertFalse(trimmed)
        self.assertEqual(out, qs)


if __name__ == "__main__":
    unittest.main()
