"""settings.auxiliary_chat_model_id"""

from __future__ import annotations

import unittest
from unittest.mock import patch

from lawbot.config import settings


class TestAuxiliaryModelTier(unittest.TestCase):
    def test_primary_uses_chat_model(self):
        with (
            patch.object(settings, "chat_model", "BIG"),
            patch.object(settings, "chat_model_fast", "SMALL"),
            patch.object(settings, "lawbot_auxiliary_model_tier", "primary"),
        ):
            self.assertEqual(settings.auxiliary_chat_model_id(), "BIG")

    def test_fast_uses_fast_model(self):
        with (
            patch.object(settings, "chat_model", "BIG"),
            patch.object(settings, "chat_model_fast", "SMALL"),
            patch.object(settings, "lawbot_auxiliary_model_tier", "fast"),
        ):
            self.assertEqual(settings.auxiliary_chat_model_id(), "SMALL")


if __name__ == "__main__":
    unittest.main()
