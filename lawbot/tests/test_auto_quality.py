"""Server-side polish routing — no UI required."""

from __future__ import annotations

import unittest

from lawbot.auto_quality import resolve_polish_second_pass
from lawbot.intent import CHAT_TASK_STRENGTHEN_FILING, CHAT_TASK_VERIFY_CITATIONS


class TestAutoQuality(unittest.TestCase):
    def test_connectivity_never_polishes_even_if_requested(self):
        # Smoke/ping turns never run polish — even if a client sent polish_second_pass.
        run, reason = resolve_polish_second_pass(
            requested=True,
            message="hello",
            task_hint=None,
            use_citation_audit=False,
            meta_connectivity=True,
        )
        self.assertFalse(run)
        self.assertIsNone(reason)

    def test_explicit_request(self):
        run, reason = resolve_polish_second_pass(
            requested=True,
            message="short",
            task_hint=None,
            use_citation_audit=False,
            meta_connectivity=False,
        )
        self.assertTrue(run)
        self.assertEqual(reason, "user")

    def test_auto_strengthen(self):
        run, reason = resolve_polish_second_pass(
            requested=False,
            message="fix this",
            task_hint=CHAT_TASK_STRENGTHEN_FILING,
            use_citation_audit=False,
            meta_connectivity=False,
        )
        self.assertTrue(run)
        self.assertEqual(reason, "auto_strengthen_filing")

    def test_auto_long_message(self):
        long_msg = "x" * 1600
        run, reason = resolve_polish_second_pass(
            requested=False,
            message=long_msg,
            task_hint=None,
            use_citation_audit=False,
            meta_connectivity=False,
        )
        self.assertTrue(run)
        self.assertEqual(reason, "auto_long_message")

    def test_skip_polish_short_when_case_lookup_off(self):
        run, reason = resolve_polish_second_pass(
            requested=False,
            message="What is hearsay?",
            task_hint=None,
            use_citation_audit=False,
            meta_connectivity=False,
            retrieval_skipped=True,
        )
        self.assertFalse(run)
        self.assertEqual(reason, "auto_skip_quick_no_case_lookup")

    def test_long_paste_still_polishes_when_case_lookup_off(self):
        long_msg = "x" * 1600
        run, reason = resolve_polish_second_pass(
            requested=False,
            message=long_msg,
            task_hint=None,
            use_citation_audit=False,
            meta_connectivity=False,
            retrieval_skipped=True,
        )
        self.assertTrue(run)
        self.assertEqual(reason, "auto_long_message")

    def test_auto_verify_citations_task(self):
        run, reason = resolve_polish_second_pass(
            requested=False,
            message="Check these cites",
            task_hint=CHAT_TASK_VERIFY_CITATIONS,
            use_citation_audit=False,
            meta_connectivity=False,
        )
        self.assertTrue(run)
        self.assertEqual(reason, "auto_verify_citations")

    def test_auto_citation_audit_substantive(self):
        msg = "y" * 100
        run, reason = resolve_polish_second_pass(
            requested=False,
            message=msg,
            task_hint=None,
            use_citation_audit=True,
            meta_connectivity=False,
        )
        self.assertTrue(run)
        self.assertEqual(reason, "auto_citation_audit")

    def test_no_auto_tiny_message_even_with_audit_flag(self):
        run, reason = resolve_polish_second_pass(
            requested=False,
            message="x" * 40,
            task_hint=None,
            use_citation_audit=True,
            meta_connectivity=False,
        )
        self.assertFalse(run)
        self.assertIsNone(reason)


if __name__ == "__main__":
    unittest.main()
