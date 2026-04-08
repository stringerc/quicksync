"""reasoning_depth.should_run_reasoning_pass"""

from __future__ import annotations

import unittest
from unittest.mock import patch

from lawbot.config import settings
from lawbot.reasoning_depth import should_run_reasoning_pass


class TestReasoningDepth(unittest.TestCase):
    def test_never_when_setting_off(self):
        with patch.object(settings, "lawbot_reasoning_pass", "never"):
            self.assertFalse(
                should_run_reasoning_pass(
                    user_message="x" * 2000,
                    document_mode=True,
                    audit_mode=False,
                    task_hint=None,
                    meta_connectivity_hint=False,
                    polish_pass_only=False,
                )
            )

    def test_document_mode(self):
        with patch.object(settings, "lawbot_reasoning_pass", "auto"):
            self.assertTrue(
                should_run_reasoning_pass(
                    user_message="short",
                    document_mode=True,
                    audit_mode=False,
                    task_hint=None,
                    meta_connectivity_hint=False,
                    polish_pass_only=False,
                )
            )

    def test_polish_skipped(self):
        with patch.object(settings, "lawbot_reasoning_pass", "auto"):
            self.assertFalse(
                should_run_reasoning_pass(
                    user_message="x" * 2000,
                    document_mode=True,
                    audit_mode=False,
                    task_hint=None,
                    meta_connectivity_hint=False,
                    polish_pass_only=True,
                )
            )

    def test_long_message(self):
        with patch.object(settings, "lawbot_reasoning_pass", "auto"):
            self.assertTrue(
                should_run_reasoning_pass(
                    user_message="a" * 1300,
                    document_mode=False,
                    audit_mode=False,
                    task_hint=None,
                    meta_connectivity_hint=False,
                    polish_pass_only=False,
                )
            )

    def test_brief_skipped(self):
        with patch.object(settings, "lawbot_reasoning_pass", "auto"):
            self.assertFalse(
                should_run_reasoning_pass(
                    user_message="hello there",
                    document_mode=False,
                    audit_mode=False,
                    task_hint=None,
                    meta_connectivity_hint=False,
                    polish_pass_only=False,
                    answer_depth="brief",
                )
            )


if __name__ == "__main__":
    unittest.main()
