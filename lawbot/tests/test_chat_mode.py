"""Citation audit vs conversational routing."""

from __future__ import annotations

import unittest

from lawbot.chat_mode import should_use_citation_audit
from lawbot.intent import CHAT_TASK_STRENGTHEN_FILING, CHAT_TASK_VERIFY_CITATIONS
from lawbot.schemas import ChatIn


class TestChatMode(unittest.TestCase):
    def test_simple_meta_question_conversational(self):
        body = ChatIn(message="is this working correctly?", session_id=None, search_case_law=True)
        self.assertFalse(
            should_use_citation_audit(body, 0, None, "full", 0),
        )

    def test_citations_in_text_forces_audit(self):
        body = ChatIn(message="Kellos v. Sawilowsky", session_id=None, search_case_law=True)
        self.assertTrue(should_use_citation_audit(body, 1, None, "full", 0))

    def test_vault_chunks_long_message_forces_audit(self):
        body = ChatIn(message="x" * 501, session_id=None, search_case_law=True)
        self.assertTrue(should_use_citation_audit(body, 0, None, "full", 2))

    def test_vault_chunks_short_message_stays_conversational(self):
        """Noisy retrieval for vague short queries should not force audit headers."""
        body = ChatIn(message="hello", session_id=None, search_case_law=True)
        self.assertFalse(should_use_citation_audit(body, 0, None, "full", 3))

    def test_verify_task_forces_audit(self):
        body = ChatIn(message="verify my citations", session_id=None, search_case_law=True)
        self.assertTrue(
            should_use_citation_audit(body, 0, CHAT_TASK_VERIFY_CITATIONS, "full", 0),
        )

    def test_strengthen_task_stays_conversational_not_audit(self):
        """Drafting-first: full audit stack off so replies are not 'Vault vs not' matrices."""
        body = ChatIn(message="x", session_id=None, search_case_law=True)
        self.assertFalse(
            should_use_citation_audit(body, 99, CHAT_TASK_STRENGTHEN_FILING, "auto", 5),
        )

    def test_auto_label_forces_audit(self):
        body = ChatIn(message="x", session_id=None, search_case_law=True)
        self.assertTrue(should_use_citation_audit(body, 0, None, "auto", 0))

    def test_api_review_pass_forces_audit(self):
        body = ChatIn(message="hi", session_id=None, search_case_law=True, review_pass="appendix")
        self.assertTrue(should_use_citation_audit(body, 0, None, "full", 0))


if __name__ == "__main__":
    unittest.main()
