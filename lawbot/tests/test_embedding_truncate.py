"""Embedding helpers: truncation avoids provider token limits."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from lawbot.embedding_client import _truncate_for_embed


class TestEmbeddingTruncate(unittest.TestCase):
    def test_short_unchanged(self):
        self.assertEqual(_truncate_for_embed("hello"), "hello")

    def test_long_truncated(self):
        class S:
            session_rag_embed_max_chars = 400

        with patch("lawbot.embedding_client.settings", S()):
            s = "a" * 500
            out = _truncate_for_embed(s)
            self.assertEqual(len(out), 400)
            self.assertTrue(out.startswith("aaa"))


if __name__ == "__main__":
    unittest.main()
