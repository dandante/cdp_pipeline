#!/usr/bin/env python3

"""
Test that warnings are issued for problematic breakpoint usage.
"""

import unittest
import warnings

from cdp_pipeline import Breakpoint


class TestBreakpointWarnings(unittest.TestCase):
    """Test warnings for problematic breakpoint usage."""

    def test_beyond_duration_warning(self):
        """Test warning when absolute time is beyond file duration."""
        # Create breakpoint with absolute time that will be beyond short file
        bp = Breakpoint()
        bp.add(0.0, 0.0)
        bp.add(0.5, 1.0)      # 0.5 seconds
        bp.add("50%", 0.5)
        bp.add("100%", 0.0)

        # Convert with short duration - should trigger warning
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = bp.to_absolute_times(0.3)

            # Should have issued a warning
            self.assertGreater(len(w), 0, "Expected warning for time beyond duration")
            self.assertIn("beyond file duration", str(w[0].message))

            # Result should still be valid (4 points, sorted by time)
            self.assertEqual(len(result), 4)
            # Check sorting
            for i in range(len(result) - 1):
                self.assertLessEqual(result[i][0], result[i + 1][0])

    def test_safe_usage(self):
        """Test that no warning is issued for safe usage."""
        # Create breakpoint with only percentages
        bp = Breakpoint()
        bp.add("0%", 0.0)
        bp.add("50%", 1.0)
        bp.add("100%", 0.0)

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = bp.to_absolute_times(0.3)

            # Should not have issued a warning
            self.assertEqual(len(w), 0, "No warning expected for percentage-only breakpoints")

            # Result should be valid (3 points)
            self.assertEqual(len(result), 3)
            self.assertAlmostEqual(result[0][0], 0.0)
            self.assertAlmostEqual(result[1][0], 0.15)
            self.assertAlmostEqual(result[2][0], 0.3)


if __name__ == "__main__":
    unittest.main()
