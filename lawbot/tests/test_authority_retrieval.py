"""Authority-pass CourtListener query bundles."""

import unittest

from lawbot.authority_retrieval import (
    build_authority_pass_queries,
    effective_max_queries,
    merge_queries_with_authority_cap,
)


class TestAuthorityRetrieval(unittest.TestCase):
    def test_effective_max_queries_scales_down(self):
        self.assertEqual(effective_max_queries(1000), 10)
        self.assertEqual(effective_max_queries(30_000), 7)
        self.assertEqual(effective_max_queries(60_000), 5)

    def test_short_message_returns_empty_pack(self):
        self.assertEqual(build_authority_pass_queries("hello"), [])

    def test_filing_message_gets_ga_pack(self):
        msg = (
            "strengthen this answer\n\nIN THE MAGISTRATE COURT\n"
            "Plaintiff v. Defendant\nmalpractice counterclaim discovery\n" + "x" * 300
        )
        qs = build_authority_pass_queries(msg, {})
        self.assertGreaterEqual(len(qs), 3)
        joined = " ".join(qs).lower()
        self.assertIn("georgia", joined)
        self.assertIn("malpractice", joined)

    def test_merge_respects_cap(self):
        base = [f"query-{i}" for i in range(8)]
        msg = "motion to dismiss Georgia answer counterclaim " + "word " * 200
        merged = merge_queries_with_authority_cap(
            base,
            msg,
            {},
            include_authority_pass=True,
            max_queries=10,
        )
        self.assertLessEqual(len(merged), 10)

    def test_merge_dedupes(self):
        base = ["Georgia legal malpractice"]
        msg = "answer discovery Gwinnett magistrate " + "a" * 250
        merged = merge_queries_with_authority_cap(
            base,
            msg,
            {},
            include_authority_pass=True,
            max_queries=20,
        )
        lowered = [m.lower() for m in merged]
        self.assertEqual(len(lowered), len(set(lowered)))


if __name__ == "__main__":
    unittest.main()
