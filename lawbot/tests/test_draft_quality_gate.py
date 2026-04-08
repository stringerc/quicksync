"""Deterministic draft quality scorecard."""

from __future__ import annotations

import unittest

from lawbot.draft_quality_gate import analyze_draft_quality, build_draft_shipping


class TestDraftQualityGate(unittest.TestCase):
    def test_clean_short_reply_all_pass(self):
        r = analyze_draft_quality(
            "Here is a clear answer about probable cause in two sentences. It depends on the totality.",
            user_message="What is probable cause?",
            document_mode=True,
        )
        self.assertEqual(r["checks_total"], 8)
        self.assertTrue(r["all_passed"])
        self.assertEqual(r["score_percent"], 100)
        self.assertEqual(r["score_percent_unweighted"], 100)

    def test_tbd_fails_placeholder(self):
        r = analyze_draft_quality(
            "The court should grant TBD relief here.",
            user_message="Draft a motion",
            document_mode=True,
        )
        self.assertFalse(r["all_passed"])
        ids = [c["id"] for c in r["checks"] if not c["passed"]]
        self.assertIn("no_placeholders", ids)

    def test_tbd_fee_line_at_trial_does_not_fail_placeholder(self):
        """Real pleadings use 'TBD' for amounts to be fixed at trial — not a template leak."""
        r = analyze_draft_quality(
            "TBD — Attorney's fees and litigation costs under O.C.G.A. § 13-6-11, in an amount to be determined at trial.",
            user_message="Polish this answer",
            document_mode=True,
        )
        ph = next(c for c in r["checks"] if c["id"] == "no_placeholders")
        self.assertTrue(ph["passed"])

    def test_internal_label_fails(self):
        r = analyze_draft_quality(
            "See SOURCE CHUNKS for support.",
            user_message="Hi",
            document_mode=True,
        )
        self.assertFalse(r["all_passed"])

    def test_long_drafting_needs_structure(self):
        user = "Strengthen this motion to dismiss\n\n" + ("x" * 500)
        body = ("Intro paragraph without headings.\n\n" * 120).strip()
        self.assertGreater(len(body), 2200)
        r = analyze_draft_quality(body, user_message=user, document_mode=True, citation_audit=False)
        struct = next(c for c in r["checks"] if c["id"] == "long_reply_structure")
        self.assertFalse(struct["passed"])

    def test_long_with_heading_passes_structure(self):
        user = "Strengthen this motion\n\n" + ("y" * 500)
        body = "## Background\n\n" + ("Para.\n\n" * 80)
        r = analyze_draft_quality(body, user_message=user, document_mode=True)
        struct = next(c for c in r["checks"] if c["id"] == "long_reply_structure")
        self.assertTrue(struct["passed"])

    def test_citation_audit_skips_structure_check(self):
        user = "Strengthen this motion\n\n" + ("z" * 500)
        body = "**Sources in vault:** None.\n\n" + ("Paragraph.\n\n" * 200)
        self.assertGreater(len(body), 2200)
        r = analyze_draft_quality(body, user_message=user, document_mode=True, citation_audit=True)
        struct = next(c for c in r["checks"] if c["id"] == "long_reply_structure")
        self.assertTrue(struct["passed"])
        self.assertIn("citation-audit", struct["detail"])

    def test_vault_quote_id_must_match(self):
        r = analyze_draft_quality(
            'Quote: <quote chunk="chk_bad">text</quote>',
            user_message="x",
            vault_chunk_ids=["chk_ok"],
            document_mode=True,
        )
        v = next(c for c in r["checks"] if c["id"] == "vault_quote_ids")
        self.assertFalse(v["passed"])

    def test_build_draft_shipping_none_without_report(self):
        self.assertIsNone(build_draft_shipping(None, verification_ok=True, draft_judge=None))

    def test_build_draft_shipping_happy_path(self):
        r = analyze_draft_quality(
            "Here is a clear answer about probable cause in two sentences. It depends on the totality.",
            user_message="What is probable cause?",
            document_mode=True,
        )
        s = build_draft_shipping(r, verification_ok=True, draft_judge=None)
        self.assertIsNotNone(s)
        self.assertTrue(s["ok"])
        self.assertTrue(s["deterministic_ok"])
        self.assertTrue(s["quote_verification_ok"])
        self.assertIsNone(s["judge_ok"])

    def test_build_draft_shipping_fails_on_quote_verification(self):
        r = analyze_draft_quality(
            "Here is a clear answer about probable cause in two sentences. It depends on the totality.",
            user_message="What is probable cause?",
            document_mode=True,
        )
        s = build_draft_shipping(r, verification_ok=False, draft_judge=None)
        self.assertIsNotNone(s)
        self.assertFalse(s["ok"])
        self.assertFalse(s["quote_verification_ok"])

    def test_build_draft_shipping_optional_judge(self):
        r = analyze_draft_quality(
            "Here is a clear answer about probable cause in two sentences. It depends on the totality.",
            user_message="What is probable cause?",
            document_mode=True,
        )
        s = build_draft_shipping(
            r,
            verification_ok=True,
            draft_judge={"parse_ok": True, "clarity": 4, "structure": 3},
        )
        self.assertIsNotNone(s)
        self.assertTrue(s["judge_ok"])
        self.assertTrue(s["ok"])
        s2 = build_draft_shipping(
            r,
            verification_ok=True,
            draft_judge={"parse_ok": True, "clarity": 2, "structure": 3},
        )
        self.assertIsNotNone(s2)
        self.assertFalse(s2["judge_ok"])
        self.assertFalse(s2["ok"])

    def test_fee_1311_thin_may_fail(self):
        """Count Four with almost no prong-specific facts should not satisfy substance heuristic."""
        thin = (
            "INTRO " * 2500
            + "\n\nCOUNT FOUR — ATTORNEY FEES (O.C.G.A. § 13-6-11)\n\n"
            + "Counter-Plaintiff seeks attorney's fees. End of count.\n\n"
            + "PRAYER\n\nRelief.\n"
        )
        self.assertGreater(len(thin), 2000)
        r = analyze_draft_quality(thin, user_message="Strengthen this\n\n" + "x" * 600, document_mode=True)
        fee = next(c for c in r["checks"] if c["id"] == "fee_1311_substance")
        self.assertFalse(fee["passed"])

    def test_editor_overview_boilerplate_fails(self):
        body = (
            "# Answer\n\n" + ("Paragraph.\n\n" * 400)
            + "\n---\n## Editor's overview (not for filing)\n\n"
            "### Preservation checklist\nThe revised pleading preserves all original allegations.\n\n"
            "### Delta vs user's prior version\nThe primary changes are reorganization for clarity and minor wording.\n"
        )
        self.assertGreater(len(body), 3500)
        r = analyze_draft_quality(
            body,
            user_message="Strengthen filing\n\n" + ("y" * 800),
            document_mode=True,
        )
        ed = next(c for c in r["checks"] if c["id"] == "editor_overview_depth")
        self.assertFalse(ed["passed"])


if __name__ == "__main__":
    unittest.main()
