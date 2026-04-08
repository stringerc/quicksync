"""ChatRateLimiter"""

from __future__ import annotations

import unittest

from lawbot.rate_limit import ChatRateLimiter


class TestRateLimit(unittest.TestCase):
    def test_disabled_allows_all(self):
        lim = ChatRateLimiter()
        for _ in range(100):
            self.assertTrue(lim.allow("1.2.3.4", 0))

    def test_cap_blocks(self):
        lim = ChatRateLimiter()
        ip = "10.0.0.1"
        for i in range(3):
            self.assertTrue(lim.allow(ip, 3), f"iteration {i}")
        self.assertFalse(lim.allow(ip, 3))


if __name__ == "__main__":
    unittest.main()
