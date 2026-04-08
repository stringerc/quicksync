"""Unit tests for empty-vault answer sanitization (no invented citations)."""

import sqlite3
import unittest

from lawbot.db import SCHEMA

from lawbot.chat_service import (
    _finalize_answer,
    _sanitize_audit_empty_vault_answer,
    _sanitize_document_draft_empty_vault,
    _sanitize_empty_vault_answer,
    _strip_assistant_filing_preamble,
    _strip_audit_empty_vault_spam_lines,
    _strip_hallucinated_citation_lines,
    _strip_quote_tags_unless_allowed,
    _truncate_copy_paste_loop,
    _truncate_paragraph_loops,
    compact_timeline_snippets,
)


class TestEmptyVaultSanitize(unittest.TestCase):
    def test_strip_assistant_filing_preamble(self):
        raw = "**Complete Revised Filing**\n\n# DEFENDANT'S ANSWER\n"
        out = _strip_assistant_filing_preamble(raw)
        self.assertTrue(out.startswith("# DEFENDANT"))
        self.assertNotIn("Complete Revised", out)

    def test_compact_timeline_truncates_and_limits(self):
        long_paste = "x" * 3000
        snippets = ["short", long_paste, "last"]
        out = compact_timeline_snippets(snippets, max_items=8, max_chars=400)
        self.assertEqual(len(out), 3)
        self.assertEqual(out[0], "short")
        self.assertIn("omitted", out[1].lower())
        self.assertEqual(out[2], "last")

    def test_strip_removes_ocga_and_case_lines(self):
        text = "Good line.\n1. O.C.G.A. § 9-3-25\nAnother good."
        out = _strip_hallucinated_citation_lines(text)
        self.assertIn("Good line", out)
        self.assertIn("Another good", out)
        self.assertNotIn("O.C.G.A.", out)

    def test_strip_quote_tags_when_no_vault(self):
        t = 'Intro <quote chunk="chk_XXXXX">fake</quote> outro'
        out = _strip_quote_tags_unless_allowed(t, [])
        self.assertNotIn("<quote", out)
        self.assertIn("Intro", out)
        self.assertIn("outro", out)

    def test_audit_empty_strips_url_spam_lines(self):
        raw = (
            "**Sources in vault:** None\n\n"
            "Please provide SOURCE CHUNKS.\n"
            "* law.justia.com\n"
            "Helpful line without URLs.\n"
        )
        out = _sanitize_audit_empty_vault_answer(raw)
        self.assertNotIn("justia", out.lower())
        self.assertIn("Helpful line without URLs", out)

    def test_strip_spam_function_only(self):
        t = "Visit https://example.com now.\nOK line.\n"
        self.assertNotIn("example.com", _strip_audit_empty_vault_spam_lines(t))

    def test_audit_strips_top_appellate_echo_line(self):
        raw = (
            "**Sources in vault:** None\n\n**Verified citations:** None.\n\n"
            "Rewrite like a top appellate attorney: use clear thesis.\n"
            "Good line about structure.\n"
        )
        out = _sanitize_audit_empty_vault_answer(raw)
        self.assertNotIn("top appellate", out.lower())
        self.assertIn("Good line about structure", out)

    def test_audit_empty_strips_ocga_lists(self):
        raw = (
            "**Sources in vault:** None\n\n"
            "1. O.C.G.A. § 9-3-25 — fake from memory.\n"
            "Discussion without cite line."
        )
        out = _sanitize_audit_empty_vault_answer(raw)
        self.assertNotIn("O.C.G.A.", out)
        self.assertIn("Discussion without cite line", out)

    def test_strip_removes_meta_chunk_and_roleplay_lines(self):
        text = "Helpful.\nWithout access to allowed chunk IDs we cannot verify.\nSuitable for a top 0.01% attorney.\nMore helpful."
        out = _strip_hallucinated_citation_lines(text)
        self.assertIn("Helpful", out)
        self.assertNotIn("allowed chunk", out.lower())
        self.assertNotIn("0.01%", out)

    def test_truncate_paragraph_loops(self):
        p = "First unique.\n\nSame paragraph\n\nSame paragraph\n\nSame paragraph"
        out = _truncate_paragraph_loops(p, max_paragraphs=10)
        self.assertEqual(out.count("Same paragraph"), 1)

    def test_truncate_copy_paste_loop(self):
        block = "PART" * 500  # >1500 chars
        doubled = block + block
        out = _truncate_copy_paste_loop(doubled)
        self.assertLess(len(out), len(doubled))
        self.assertEqual(out, block.rstrip())

    def test_sanitize_falls_back_when_only_cites(self):
        junk = "\n".join(
            [
                "1. O.C.G.A. § 15-10-45(d)",
                "2. Kellos v. Sawilowsky, 254 Ga. 4",
                "3. Cox-Ott v. Barnes, 2025 Ga. LEXIS 98",
            ]
        )
        out = _sanitize_empty_vault_answer(junk)
        self.assertNotIn("O.C.G.A.", out)
        self.assertNotIn("Kellos", out)
        self.assertIn("**Sources in vault:**", out)
        self.assertIn("no court excerpts", out.lower())

    def test_finalize_answer_strips_without_chunks(self):
        conn = sqlite3.connect(":memory:")
        try:
            conn.executescript(SCHEMA)
            raw = "Here is analysis.\n\nO.C.G.A. § 9-3-25 applies.\n\nMore analysis."
            out = _finalize_answer(
                raw,
                conn,
                [],
                "sid",
                "test-model",
                True,
                "No opinions were added to the vault for this search.",
                False,
                llm_backend_used="openai_compatible",
            )
            self.assertNotIn("O.C.G.A.", out["answer"])
            self.assertIn("No opinions were added to the vault", out["answer"])
            self.assertTrue(out["vault_empty"])
        finally:
            conn.close()

    def test_document_mode_preserves_long_draft_no_paragraph_cap(self):
        """Regression: conversational sanitizer capped at 16 paragraphs and cut off pleadings."""
        conn = sqlite3.connect(":memory:")
        try:
            conn.executescript(SCHEMA)
            blocks = [f"## PART {i}\n\nBody text for section {i}.\n\nO.C.G.A. § 9-11-9.1 mentioned." for i in range(22)]
            raw = "\n\n".join(blocks)
            out = _finalize_answer(
                raw,
                conn,
                [],
                "sid",
                "test-model",
                True,
                None,
                False,
                audit_mode=False,
                document_mode=True,
                llm_backend_used="openai_compatible",
            )
            self.assertIn("PART 21", out["answer"])
            self.assertIn("O.C.G.A.", out["answer"])
            self.assertGreater(len(out["answer"]), len(raw) * 0.9)
        finally:
            conn.close()

    def test_sanitize_document_draft_only_trims_duplicate_loops(self):
        long_unique = "\n\n".join([f"Block {i} unique text." for i in range(30)])
        out = _sanitize_document_draft_empty_vault(long_unique)
        self.assertIn("Block 29", out)


if __name__ == "__main__":
    unittest.main()
