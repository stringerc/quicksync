"""Daily Anthropic escalation counter (SQLite)."""

from __future__ import annotations

import sqlite3
import unittest
from unittest.mock import patch

from lawbot.config import settings
from lawbot.db import SCHEMA
from lawbot.usage_limits import (
    METRIC_ANTHROPIC_ESCALATION,
    can_use_anthropic_escalation,
    get_daily_count,
    record_anthropic_escalation,
)


class TestUsageLimits(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.executescript(SCHEMA)

    def tearDown(self):
        self.conn.close()

    def test_unlimited_when_negative_cap(self):
        with patch.object(settings, "max_anthropic_escalations_per_day", -1):
            self.assertTrue(can_use_anthropic_escalation(self.conn))

    def test_zero_cap_blocks(self):
        with patch.object(settings, "max_anthropic_escalations_per_day", 0):
            self.assertFalse(can_use_anthropic_escalation(self.conn))

    def test_increment_and_cap(self):
        with patch.object(settings, "max_anthropic_escalations_per_day", 2):
            self.assertTrue(can_use_anthropic_escalation(self.conn))
            record_anthropic_escalation(self.conn)
            self.assertEqual(get_daily_count(self.conn, METRIC_ANTHROPIC_ESCALATION), 1)
            record_anthropic_escalation(self.conn)
            self.assertFalse(can_use_anthropic_escalation(self.conn))


if __name__ == "__main__":
    unittest.main()
