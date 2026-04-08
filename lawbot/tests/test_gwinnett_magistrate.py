"""Gwinnett County Magistrate local template detection."""

from __future__ import annotations

import unittest

from lawbot.chat_service import build_user_block
from lawbot.gwinnett_magistrate import (
    GWINNETT_MAGISTRATE_CIVIL_FORMS_URL,
    gwinnett_magistrate_drafting_relevant,
    should_inject_gwinnett_magistrate_template,
)
from lawbot.intent import CHAT_TASK_STRENGTHEN_FILING


class TestGwinnettMagistrate(unittest.TestCase):
    def test_not_relevant_without_civil_cue(self):
        self.assertFalse(
            gwinnett_magistrate_drafting_relevant("I live in Gwinnett County and need tax advice.", {})
        )

    def test_relevant_gwinnett_plus_magistrate(self):
        self.assertTrue(
            gwinnett_magistrate_drafting_relevant(
                "Draft an answer for Gwinnett Magistrate Court.", {}
            )
        )

    def test_relevant_profile_jurisdiction(self):
        self.assertTrue(
            gwinnett_magistrate_drafting_relevant(
                "Help with my counterclaim defenses.",
                {"jurisdiction": "Gwinnett County, Georgia"},
            )
        )

    def test_inject_document_mode(self):
        self.assertTrue(
            should_inject_gwinnett_magistrate_template(
                "Answer for Gwinnett magistrate",
                {},
                document_mode=True,
                task_hint=None,
                audit_mode=False,
            )
        )

    def test_inject_strengthen(self):
        self.assertTrue(
            should_inject_gwinnett_magistrate_template(
                "Strengthen this answer — Gwinnett County magistrate",
                {},
                document_mode=False,
                task_hint=CHAT_TASK_STRENGTHEN_FILING,
                audit_mode=False,
            )
        )

    def test_no_inject_plain_chat(self):
        self.assertFalse(
            should_inject_gwinnett_magistrate_template(
                "What is an answer in Gwinnett magistrate court?",
                {},
                document_mode=False,
                task_hint=None,
                audit_mode=False,
            )
        )

    def test_build_user_block_contains_forms_url(self):
        ub = build_user_block(
            "x",
            [],
            "",
            [],
            [],
            gwinnett_magistrate_template=f"FORMS: {GWINNETT_MAGISTRATE_CIVIL_FORMS_URL}",
            document_mode=True,
        )
        self.assertIn("gwinnettcourts.com/magistrate/civil-filing-forms", ub)


if __name__ == "__main__":
    unittest.main()
