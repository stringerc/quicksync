"""tail_health rolling metrics."""

import unittest

from lawbot.tail_health import (
    record_http_429,
    record_latency_ms,
    reset_tail_health_for_tests,
    snapshot_all_backends,
    snapshot_for_backend,
)


class TestTailHealth(unittest.TestCase):
    def setUp(self) -> None:
        reset_tail_health_for_tests()

    def tearDown(self) -> None:
        reset_tail_health_for_tests()

    def test_latency_and_429(self):
        record_latency_ms("openai_compatible", 120.0)
        record_latency_ms("openai_compatible", 80.0)
        record_http_429("openai_compatible")
        s = snapshot_for_backend("openai_compatible")
        self.assertEqual(s["tail_latency_samples"], 2)
        self.assertIsNotNone(s["tail_sec_since_429"])
        self.assertGreaterEqual(s["tail_rate_limit_events_1h"], 1)
        self.assertIsNotNone(s["tail_median_latency_ms_10"])

    def test_snapshot_all_has_both_backends(self):
        record_latency_ms("anthropic", 500.0)
        all_b = snapshot_all_backends()
        self.assertIn("tail_anth_median_latency_ms_10", all_b)
        self.assertIn("tail_oc_median_latency_ms_10", all_b)


if __name__ == "__main__":
    unittest.main()
