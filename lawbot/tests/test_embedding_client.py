"""embedding_client NVIDIA extras."""

from __future__ import annotations

from unittest import TestCase
from unittest.mock import patch

from lawbot.config import settings
from lawbot.embedding_client import _nv_embed_extra


class TestNvEmbedExtra(TestCase):
    def test_nv_embedqa_sets_input_type(self):
        with patch.object(settings, "lawbot_embedding_model", "nvidia/nv-embedqa-e5-v5"):
            self.assertEqual(_nv_embed_extra("query"), {"input_type": "query"})
            self.assertEqual(_nv_embed_extra("passage"), {"input_type": "passage"})

    def test_other_models_no_extra(self):
        with patch.object(settings, "lawbot_embedding_model", "text-embedding-3-small"):
            self.assertIsNone(_nv_embed_extra("query"))


if __name__ == "__main__":
    import unittest

    unittest.main()
