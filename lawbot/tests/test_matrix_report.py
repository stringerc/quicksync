"""Matrix coverage report smoke tests."""

from __future__ import annotations

import unittest

from lawbot.eval.matrix_report import build_report


class TestMatrixReport(unittest.TestCase):
    def test_build_report_shape(self):
        r = build_report()
        self.assertIn("golden_count", r)
        self.assertIn("cells", r)
        self.assertGreaterEqual(r["golden_count"], 1)
        self.assertIsInstance(r["cells"], dict)

    def test_required_coverage_fields_when_taxonomy_present(self):
        r = build_report()
        if (r.get("required_cell_count") or 0) > 0:
            self.assertIn("required_cells_covered", r)
            self.assertIn("missing_required_cells", r)


if __name__ == "__main__":
    unittest.main()
