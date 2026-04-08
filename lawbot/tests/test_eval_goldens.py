"""Golden harness smoke test."""

import unittest

from lawbot.eval.run_goldens import run_all


class TestEvalGoldens(unittest.TestCase):
    def test_run_all_exits_zero(self):
        self.assertEqual(run_all(verbose=False), 0)


if __name__ == "__main__":
    unittest.main()
