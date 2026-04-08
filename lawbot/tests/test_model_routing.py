"""OpenAI-compatible model tier selection."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from lawbot.intent import CHAT_TASK_VERIFY_CITATIONS
from lawbot.model_routing import select_chat_model


class TestModelRouting(unittest.TestCase):
    def test_substantive_uses_primary_model(self):
        with (
            patch("lawbot.model_routing.settings.chat_model", "PRIMARY"),
            patch("lawbot.model_routing.settings.chat_model_fast", "FAST"),
        ):
            self.assertEqual(
                select_chat_model(
                    user_message="How do I strengthen this counterclaim under Georgia law?",
                    meta_connectivity_hint=False,
                ),
                "PRIMARY",
            )

    def test_ping_uses_fast(self):
        with (
            patch("lawbot.model_routing.settings.chat_model", "PRIMARY"),
            patch("lawbot.model_routing.settings.chat_model_fast", "FAST"),
        ):
            self.assertEqual(
                select_chat_model(
                    user_message="ping",
                    meta_connectivity_hint=False,
                ),
                "FAST",
            )

    def test_connectivity_hint_uses_fast(self):
        with (
            patch("lawbot.model_routing.settings.chat_model", "PRIMARY"),
            patch("lawbot.model_routing.settings.chat_model_fast", "FAST"),
        ):
            self.assertEqual(
                select_chat_model(
                    user_message="testing to see if this works",
                    meta_connectivity_hint=True,
                ),
                "FAST",
            )

    def test_fast_unset_falls_back_to_primary(self):
        with (
            patch("lawbot.model_routing.settings.chat_model", "ONLY"),
            patch("lawbot.model_routing.settings.chat_model_fast", ""),
        ):
            self.assertEqual(
                select_chat_model(user_message="ping", meta_connectivity_hint=False),
                "ONLY",
            )

    def test_max_tier_when_set_and_high_stakes(self):
        with (
            patch("lawbot.model_routing.settings.chat_model", "PRIMARY"),
            patch("lawbot.model_routing.settings.chat_model_fast", "FAST"),
            patch("lawbot.model_routing.settings.chat_model_max", "MAX"),
        ):
            self.assertEqual(
                select_chat_model(
                    user_message="x" * 1600,
                    meta_connectivity_hint=False,
                    document_mode=False,
                    audit_mode=False,
                    task_hint=None,
                    polish_pass_only=False,
                ),
                "MAX",
            )

    def test_polish_pass_skips_max_tier(self):
        with (
            patch("lawbot.model_routing.settings.chat_model", "PRIMARY"),
            patch("lawbot.model_routing.settings.chat_model_fast", "FAST"),
            patch("lawbot.model_routing.settings.chat_model_max", "MAX"),
        ):
            self.assertEqual(
                select_chat_model(
                    user_message="x" * 5000,
                    meta_connectivity_hint=False,
                    document_mode=True,
                    audit_mode=True,
                    task_hint=CHAT_TASK_VERIFY_CITATIONS,
                    polish_pass_only=True,
                ),
                "PRIMARY",
            )


if __name__ == "__main__":
    unittest.main()
