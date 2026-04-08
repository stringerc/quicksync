"""
Must match lawbot/static/app.js chatTimeoutMs(messageLen, options).

Base: min(30 min, 3 min + 10ms/char). For n >= 8000, add +12 min if search_case, +12 min if two_phase.
For n >= 25000, add +8 min. Absolute max 45 min.
"""


from __future__ import annotations

import unittest


def chat_timeout_ms(
    message_len: int,
    *,
    search_case_law: bool = True,
    two_phase_filing: bool = True,
) -> int:
    n = max(0, int(message_len) if message_len is not None else 0)
    t = min(1_800_000, 180_000 + n * 10)
    if n >= 8_000:
        if search_case_law:
            t += 720_000
        if two_phase_filing:
            t += 720_000
    if n >= 25_000:
        t += 480_000
    return min(2_700_000, t)


class TestChatTimeoutFormula(unittest.TestCase):
    def test_short_message_floor(self):
        self.assertEqual(chat_timeout_ms(0), 180_000)
        self.assertEqual(chat_timeout_ms(100), 181_000)

    def test_mid_scales(self):
        self.assertEqual(chat_timeout_ms(5000), 180_000 + 50_000)

    def test_long_paste_gets_bonuses_default(self):
        """~35k chars: base 530s + 24 min search/two-phase + 8 min long-paste bonus."""
        t = chat_timeout_ms(35_000)
        self.assertEqual(t, 530_000 + 720_000 + 720_000 + 480_000)

    def test_long_paste_no_search_smaller(self):
        t = chat_timeout_ms(35_000, search_case_law=False, two_phase_filing=True)
        self.assertEqual(t, 530_000 + 720_000 + 480_000)

    def test_very_large_hits_soft_cap_plus_bonuses(self):
        """Base tops at 30 min; bonuses + long-paste tier hit absolute 45 min cap."""
        self.assertEqual(chat_timeout_ms(500_000), 2_700_000)

    def test_72k_mega_paste(self):
        """72k chars: base 900k + 24 min bonuses + 8 min tier → capped at 45 min."""
        t = chat_timeout_ms(72_000)
        self.assertEqual(t, 2_700_000)


if __name__ == "__main__":
    unittest.main()
