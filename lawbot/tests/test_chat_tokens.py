"""Max-token caps for concise replies."""

from __future__ import annotations

import unittest

from lawbot.chat_service import _chat_sampling_temperature, _max_tokens_for_chat_turn
from lawbot.intent import CHAT_TASK_STRENGTHEN_FILING, CHAT_TASK_VERIFY_CITATIONS


class TestChatMaxTokens(unittest.TestCase):
    def test_verify_citations_tight_cap(self):
        self.assertEqual(
            _max_tokens_for_chat_turn(
                document_mode=False,
                audit_mode=True,
                no_sources=True,
                user_block_len=1000,
                task_hint=CHAT_TASK_VERIFY_CITATIONS,
            ),
            3072,
        )
        self.assertEqual(
            _max_tokens_for_chat_turn(
                document_mode=False,
                audit_mode=True,
                no_sources=False,
                user_block_len=1000,
                task_hint=CHAT_TASK_VERIFY_CITATIONS,
            ),
            4096,
        )

    def test_default_chat_shorter_than_old_8192(self):
        self.assertEqual(
            _max_tokens_for_chat_turn(
                document_mode=False,
                audit_mode=False,
                no_sources=False,
                user_block_len=1000,
                task_hint=None,
            ),
            4096,
        )

    def test_conversational_tight_cap(self):
        self.assertEqual(
            _max_tokens_for_chat_turn(
                document_mode=False,
                audit_mode=False,
                no_sources=True,
                user_block_len=500,
                task_hint=None,
            ),
            1024,
        )

    def test_document_mode_uncapped_high(self):
        self.assertEqual(
            _max_tokens_for_chat_turn(
                document_mode=True,
                audit_mode=True,
                no_sources=False,
                user_block_len=1000,
                task_hint=CHAT_TASK_VERIFY_CITATIONS,
            ),
            12288,
        )


class TestChatSamplingTemperature(unittest.TestCase):
    def test_document_mode_empty_vault_tighter(self):
        self.assertEqual(
            _chat_sampling_temperature(
                no_sources=True,
                audit_mode=False,
                document_mode=True,
                task_hint=None,
                meta_connectivity_hint=False,
            ),
            0.42,
        )

    def test_document_mode_with_chunks(self):
        self.assertEqual(
            _chat_sampling_temperature(
                no_sources=False,
                audit_mode=False,
                document_mode=True,
                task_hint=None,
                meta_connectivity_hint=False,
            ),
            0.52,
        )

    def test_strengthen_with_document(self):
        self.assertEqual(
            _chat_sampling_temperature(
                no_sources=True,
                audit_mode=False,
                document_mode=True,
                task_hint=CHAT_TASK_STRENGTHEN_FILING,
                meta_connectivity_hint=False,
            ),
            0.36,
        )

    def test_connectivity_bump(self):
        self.assertEqual(
            _chat_sampling_temperature(
                no_sources=True,
                audit_mode=False,
                document_mode=True,
                task_hint=None,
                meta_connectivity_hint=True,
            ),
            0.4,
        )

    def test_polish_pass_only_temperature(self):
        self.assertEqual(
            _chat_sampling_temperature(
                no_sources=True,
                audit_mode=False,
                document_mode=True,
                task_hint=None,
                meta_connectivity_hint=False,
                polish_pass_only=True,
            ),
            0.36,
        )


if __name__ == "__main__":
    unittest.main()
