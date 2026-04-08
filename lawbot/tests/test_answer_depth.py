"""answer_depth classifier — conservative routing."""

import unittest

from lawbot.answer_depth import classify_answer_depth
from lawbot.intent import CHAT_TASK_STRENGTHEN_FILING


class TestAnswerDepth(unittest.TestCase):
    def test_brief_short_no_vault(self):
        d = classify_answer_depth(
            message="What is 9 times 7?",
            meta_connectivity=False,
            document_mode=False,
            use_citation_audit=False,
            task_hint=None,
            chunk_ids=[],
            explicit_research_query=None,
            force_authority_retrieval=False,
        )
        self.assertEqual(d.level, "brief")
        self.assertIn("short_general", d.reason)

    def test_not_brief_with_legal_hook(self):
        d = classify_answer_depth(
            message="Can I lose custody if I miss a hearing in Georgia?",
            meta_connectivity=False,
            document_mode=False,
            use_citation_audit=False,
            task_hint=None,
            chunk_ids=[],
            explicit_research_query=None,
            force_authority_retrieval=False,
        )
        self.assertEqual(d.level, "standard")

    def test_deep_document(self):
        d = classify_answer_depth(
            message="x",
            meta_connectivity=False,
            document_mode=True,
            use_citation_audit=False,
            task_hint=None,
            chunk_ids=[],
            explicit_research_query=None,
            force_authority_retrieval=False,
        )
        self.assertEqual(d.level, "deep")

    def test_deep_strengthen(self):
        d = classify_answer_depth(
            message="x" * 100,
            meta_connectivity=False,
            document_mode=False,
            use_citation_audit=False,
            task_hint=CHAT_TASK_STRENGTHEN_FILING,
            chunk_ids=[],
            explicit_research_query=None,
            force_authority_retrieval=False,
        )
        self.assertEqual(d.level, "deep")

    def test_deep_long_message(self):
        d = classify_answer_depth(
            message="word " * 400,
            meta_connectivity=False,
            document_mode=False,
            use_citation_audit=False,
            task_hint=None,
            chunk_ids=[],
            explicit_research_query=None,
            force_authority_retrieval=False,
        )
        self.assertEqual(d.level, "deep")
        self.assertIn("long", d.reason)

    def test_standard_one_chunk(self):
        d = classify_answer_depth(
            message="help",
            meta_connectivity=False,
            document_mode=False,
            use_citation_audit=False,
            task_hint=None,
            chunk_ids=["c1"],
            explicit_research_query=None,
            force_authority_retrieval=False,
        )
        self.assertEqual(d.level, "standard")
        self.assertIn("vault", d.reason)

    def test_meta_connectivity_standard(self):
        d = classify_answer_depth(
            message="testing to see if this works",
            meta_connectivity=True,
            document_mode=False,
            use_citation_audit=False,
            task_hint=None,
            chunk_ids=[],
            explicit_research_query=None,
            force_authority_retrieval=False,
        )
        self.assertEqual(d.level, "standard")


if __name__ == "__main__":
    unittest.main()
