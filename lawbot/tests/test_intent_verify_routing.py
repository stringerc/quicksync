"""Routing: citation verification intent must match natural phrasing (e.g. "verified", "make sure")."""

import unittest

from lawbot.intent import CHAT_TASK_VERIFY_CITATIONS, classify_simple_task


class TestVerifyIntentPhrasing(unittest.TestCase):
    def test_make_sure_and_verified_opener_with_long_paste(self):
        msg = (
            "can you make sure the laws/cases cited in this are all true and verified:\n\n"
            "IN THE MAGISTRATE COURT OF GWINNETT COUNTY\n"
        ) + ("PARTY NAMES AND LONG FILING TEXT.\n" * 400)

        self.assertEqual(classify_simple_task(msg), CHAT_TASK_VERIFY_CITATIONS)

    def test_verify_word_still_matches(self):
        msg = "Please verify the citations in this paragraph: Kellos v. Sawilowsky, 254 Ga. 4."
        self.assertEqual(classify_simple_task(msg), CHAT_TASK_VERIFY_CITATIONS)


if __name__ == "__main__":
    unittest.main()
