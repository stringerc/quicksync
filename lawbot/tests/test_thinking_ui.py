"""Compact vs full thinking-step UI eligibility."""

import unittest

from lawbot.intent import CHAT_TASK_VERIFY_CITATIONS
from lawbot.thinking_ui import compact_thinking_eligible


class TestCompactThinkingEligible(unittest.TestCase):
    def test_smoke_ping_compact(self):
        self.assertTrue(
            compact_thinking_eligible(
                msg_stripped="testing",
                meta_connectivity=False,
                task_hint=None,
                review_audit_label="",
                extracted_count=0,
                response_mode="chat",
                explicit_research_query=None,
                force_authority_retrieval=False,
            )
        )

    def test_verify_task_full_steps(self):
        self.assertFalse(
            compact_thinking_eligible(
                msg_stripped="verify my cites",
                meta_connectivity=False,
                task_hint=CHAT_TASK_VERIFY_CITATIONS,
                review_audit_label="",
                extracted_count=0,
                response_mode="chat",
                explicit_research_query=None,
                force_authority_retrieval=False,
            )
        )

    def test_extracted_cite_full_steps(self):
        self.assertFalse(
            compact_thinking_eligible(
                msg_stripped="Smith v. Jones",
                meta_connectivity=False,
                task_hint=None,
                review_audit_label="",
                extracted_count=1,
                response_mode="chat",
                explicit_research_query=None,
                force_authority_retrieval=False,
            )
        )

    def test_long_document_mode_full_steps(self):
        self.assertFalse(
            compact_thinking_eligible(
                msg_stripped="x" * 400,
                meta_connectivity=False,
                task_hint=None,
                review_audit_label="",
                extracted_count=0,
                response_mode="document",
                explicit_research_query=None,
                force_authority_retrieval=False,
            )
        )


if __name__ == "__main__":
    unittest.main()
