"""Second-pass polish message builder."""

from __future__ import annotations

import unittest

from lawbot.polish_pass import build_polish_second_pass_user_message


class TestPolishPass(unittest.TestCase):
    def test_contains_original_and_draft(self):
        m = build_polish_second_pass_user_message("User asks for X.", "Draft line one.\nDraft line two.")
        self.assertIn("User asks for X.", m)
        self.assertIn("Draft line one.", m)
        self.assertIn("POLISH PASS", m)
        self.assertIn("court caption", m.lower())
        self.assertIn("editor's overview", m.lower())


if __name__ == "__main__":
    unittest.main()
