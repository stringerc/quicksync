import unittest

from lawbot.intent import (
    CHAT_TASK_STRENGTHEN_FILING,
    CHAT_TASK_VERIFY_CITATIONS,
    classify_simple_task,
    is_smoke_test_message,
    extract_jurisdiction_hint,
    infer_research_query,
    is_meta_connectivity_message,
    prepare_case_law_search,
    task_directive_for_chat_task,
    user_asks_prestige_attorney_framing,
)


class TestIntent(unittest.TestCase):
    def test_explicit_research_always_used(self):
        self.assertEqual(
            infer_research_query("hi", "fourth amendment warrant"),
            "fourth amendment warrant",
        )

    def test_smoke_words_skip(self):
        for w in ("testing", "test", "ping", "hello", "hi"):
            with self.subTest(w=w):
                self.assertEqual(infer_research_query(w, None), "")

    def test_is_smoke_test_message(self):
        self.assertTrue(is_smoke_test_message("ping"))
        self.assertTrue(is_smoke_test_message("hi"))
        self.assertFalse(is_smoke_test_message("How do I win a custody motion in Georgia?"))

    def test_meta_connectivity_skips_retrieval(self):
        self.assertTrue(is_meta_connectivity_message("testing to see if this works"))
        self.assertEqual(infer_research_query("testing to see if this works", None), "")
        self.assertFalse(is_meta_connectivity_message("testing to see if I can win custody in Georgia"))

    def test_is_meta_connectivity_false_when_substantive(self):
        self.assertFalse(
            is_meta_connectivity_message("What malpractice standard applies to custody lawyers in Gwinnett?")
        )

    def test_prestige_framing_detection(self):
        self.assertTrue(user_asks_prestige_attorney_framing("Rewrite like a top 0.01% appellate attorney would."))
        self.assertTrue(user_asks_prestige_attorney_framing("Make it sound like a top appellate attorney wrote it."))
        self.assertTrue(
            user_asks_prestige_attorney_framing(
                "can we make sure that this is written in a way a top .01% appellate attorney would write it:"
            )
        )
        self.assertFalse(user_asks_prestige_attorney_framing("What is the statute of limitations for contracts?"))

    def test_rewrite_opening_beats_buried_verify_in_appendix(self):
        body = (
            "rewrite this like a top attorney would:\n\n"
            "IN THE MAGISTRATE COURT\nCOMES NOW Defendant.\n\n"
            + ("paragraph text. " * 400)
            + "\n\nHOW TO VERIFY THESE CITATIONS\nPlease verify citations using Justia.\n"
        )
        self.assertEqual(classify_simple_task(body), CHAT_TASK_STRENGTHEN_FILING)

    def test_prestige_opening_beats_buried_verify_in_appendix(self):
        body = (
            "can we make sure that this is written in a way a top .01% appellate attorney would write it:\n\n"
            "IN THE MAGISTRATE COURT\nCOMES NOW Defendant.\n\n"
            + ("paragraph text. " * 400)
            + "\n\nHOW TO VERIFY THESE CITATIONS\nPlease verify citations using Justia.\n"
        )
        self.assertEqual(classify_simple_task(body), CHAT_TASK_STRENGTHEN_FILING)

    def test_verify_in_leading_text_still_verify(self):
        self.assertEqual(
            classify_simple_task("Please verify the citations in this paragraph about O.C.G.A."),
            CHAT_TASK_VERIFY_CITATIONS,
        )

    def test_rewrite_short_non_filing_not_strengthen(self):
        self.assertIsNone(classify_simple_task("rewrite this email to sound nicer"))

    def test_short_message_skips(self):
        self.assertEqual(infer_research_query("short msg", None), "")

    def test_substantive_message_searches(self):
        q = "What are the elements of negligence in Georgia?"
        self.assertEqual(infer_research_query(q, None), q)

    def test_state_name_allows_shorter_message(self):
        q = "Is weed legal in California for adults"
        self.assertEqual(infer_research_query(q, None), q)

    def test_extract_georgia(self):
        self.assertEqual(
            extract_jurisdiction_hint("Can I get emergency custody in Georgia?"),
            "Georgia",
        )

    def test_prepare_appends_profile_jurisdiction(self):
        q = prepare_case_law_search(
            "What is the standard for modifying child custody?",
            None,
            {"jurisdiction": "Georgia"},
        )
        self.assertIn("Georgia", q)
        self.assertIn("custody", q.lower())

    def test_prepare_does_not_duplicate_place_in_message(self):
        msg = "Terry stop reasonable suspicion in Georgia"
        q = prepare_case_law_search(msg, None, {"jurisdiction": "Georgia"})
        self.assertEqual(q.count("Georgia"), 1)

    def test_classify_verify_citations(self):
        self.assertEqual(
            classify_simple_task("Please verify the cases and laws in this paragraph"),
            CHAT_TASK_VERIFY_CITATIONS,
        )
        self.assertEqual(
            classify_simple_task("check my citations for accuracy"),
            CHAT_TASK_VERIFY_CITATIONS,
        )
        self.assertIsNone(classify_simple_task("verify my email address"))

    def test_classify_strengthen_filing(self):
        self.assertEqual(
            classify_simple_task("How can I strengthen this motion to dismiss?"),
            CHAT_TASK_STRENGTHEN_FILING,
        )
        self.assertIsNone(classify_simple_task("strengthen my argument about pizza"))

    def test_task_directive_nonempty_for_known_tasks(self):
        self.assertIn("Citation verification", task_directive_for_chat_task(CHAT_TASK_VERIFY_CITATIONS) or "")
        self.assertIn("Strengthen", task_directive_for_chat_task(CHAT_TASK_STRENGTHEN_FILING) or "")

    def test_task_directive_strengthen_document_mode_full_draft(self):
        d = task_directive_for_chat_task(CHAT_TASK_STRENGTHEN_FILING, document_mode=True) or ""
        self.assertIn("complete revised pleading", d.lower())
        self.assertIn("caption", d.lower())


if __name__ == "__main__":
    unittest.main()
