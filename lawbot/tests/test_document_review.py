"""Section review helpers, automatic verification, and build_user_block integration."""

from __future__ import annotations

import unittest

from lawbot.chat_service import build_user_block
from lawbot.document_review import (
    AUTO_LONG_MESSAGE_CHARS,
    AUTO_MIN_CITATION_CANDIDATES,
    build_auto_verification_block,
    build_review_instruction_block,
    resolve_review_injection,
    should_use_auto_verification,
)


class TestDocumentReview(unittest.TestCase):
    def test_full_pass_empty_block(self):
        self.assertEqual(build_review_instruction_block(None, None), "")
        self.assertEqual(build_review_instruction_block("full", None), "")

    def test_part1_contains_focus(self):
        b = build_review_instruction_block("part1", None)
        self.assertIn("Part I", b)
        self.assertIn("DOCUMENT SECTION REVIEW", b)
        self.assertIn("Scope", b)

    def test_custom_requires_text(self):
        self.assertEqual(build_review_instruction_block("custom", None), "")
        self.assertEqual(build_review_instruction_block("custom", "   "), "")
        cu = build_review_instruction_block("custom", "Check fee setoff only")
        self.assertIn("Custom focus:", cu)
        self.assertIn("Check fee setoff only", cu)

    def test_invalid_pass_treated_as_full(self):
        self.assertEqual(build_review_instruction_block("not-a-pass", None), "")

    def test_auto_verification_block(self):
        b = build_auto_verification_block()
        self.assertIn("AUTOMATIC CITATION REVIEW", b)
        self.assertIn("entire message", b.lower())

    def test_should_use_auto_by_length(self):
        self.assertFalse(should_use_auto_verification("x" * (AUTO_LONG_MESSAGE_CHARS - 1), 0))
        self.assertTrue(should_use_auto_verification("x" * AUTO_LONG_MESSAGE_CHARS, 0))

    def test_should_use_auto_by_cite_count(self):
        self.assertFalse(should_use_auto_verification("short", AUTO_MIN_CITATION_CANDIDATES - 1))
        self.assertTrue(should_use_auto_verification("short", AUTO_MIN_CITATION_CANDIDATES))

    def test_resolve_auto_without_explicit_pass(self):
        long_msg = "x" * AUTO_LONG_MESSAGE_CHARS
        block, label = resolve_review_injection(None, None, long_msg, 0)
        self.assertEqual(label, "auto")
        self.assertIn("AUTOMATIC CITATION REVIEW", block)

    def test_resolve_explicit_wins_over_auto(self):
        long_msg = "x" * AUTO_LONG_MESSAGE_CHARS
        block, label = resolve_review_injection("part2", None, long_msg, 99)
        self.assertEqual(label, "part2")
        self.assertIn("Part II", block)
        self.assertNotIn("AUTOMATIC CITATION REVIEW", block)

    def test_build_user_block_injects_explicit_review(self):
        inj = build_review_instruction_block("part2", None)
        ub = build_user_block(
            "USER TEXT",
            [],
            "",
            [],
            [],
            review_injection=inj,
        )
        self.assertIn("DOCUMENT SECTION REVIEW", ub)
        self.assertIn("Part II", ub)
        self.assertIn("USER MESSAGE:", ub)
        self.assertIn("USER TEXT", ub)

    def test_build_user_block_injects_auto(self):
        inj = build_auto_verification_block()
        ub = build_user_block("x", [], "", [], [], review_injection=inj)
        self.assertIn("AUTOMATIC CITATION REVIEW", ub)


if __name__ == "__main__":
    unittest.main()
