"""Tests for audit retrieval merge and query building."""

import unittest

from lawbot.audit_retrieval import build_audit_queries, merge_retrieval_results
from lawbot.citation_extract import extract_citation_candidates


class TestMergeRetrieval(unittest.TestCase):
    def test_dedupes_chunk_ids(self):
        c1 = {"chunk_id": "chk_a", "label": "A", "source_url": None, "excerpt": "one"}
        c2 = {"chunk_id": "chk_a", "label": "A", "source_url": None, "excerpt": "one"}
        r = merge_retrieval_results(
            [
                {"chunks": [c1], "chunk_ids": ["chk_a"], "query_executed": True},
                {"chunks": [c2], "chunk_ids": ["chk_a"], "query_executed": True},
            ]
        )
        self.assertEqual(r["chunk_ids"], ["chk_a"])
        self.assertEqual(len(r["chunks"]), 1)

    def test_failure_flag_when_empty_and_error(self):
        r = merge_retrieval_results(
            [
                {
                    "chunks": [],
                    "chunk_ids": [],
                    "query_executed": True,
                    "retrieval_failed": True,
                    "http_status": 403,
                }
            ]
        )
        self.assertTrue(r.get("retrieval_failed"))
        self.assertEqual(r.get("http_status"), 403)


class TestBuildAuditQueries(unittest.TestCase):
    def test_includes_explicit_research_query_first(self):
        msg = "Motion practice in Georgia regarding discovery defaults."
        ex = extract_citation_candidates(msg)
        profile = {"jurisdiction": "Georgia"}
        qs = build_audit_queries(
            msg,
            ex,
            profile,
            explicit_research_query="Georgia reciprocal discovery malpractice",
        )
        self.assertGreaterEqual(len(qs), 1)
        self.assertIn("Georgia reciprocal discovery malpractice", qs[0])

    def test_caps_length(self):
        long_msg = "word " * 200 + " in Georgia."
        ex = extract_citation_candidates(long_msg)
        profile = {}
        qs = build_audit_queries(long_msg, ex, profile, None)
        self.assertLessEqual(len(qs), 6)


if __name__ == "__main__":
    unittest.main()
