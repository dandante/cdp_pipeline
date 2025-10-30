#!/usr/bin/env python3

"""
Test breakpoint automation functionality.
"""

import unittest
import warnings
from pathlib import Path

from cdp_pipeline import Breakpoint, Pipeline
from cdp_pipeline.operations import custom_operation
from cdp_pipeline.core import FileFormat, ChannelMode


class TestBreakpointCreation(unittest.TestCase):
    """Test creating breakpoints."""

    def test_add_method(self):
        """Test creating breakpoint with add() method."""
        bp = Breakpoint()
        bp.add(0.0, 5.0)
        bp.add("50%", 10.0)
        bp.add("99%", 2.0)

        self.assertEqual(len(bp), 3)

    def test_from_pairs(self):
        """Test creating breakpoint with from_pairs() class method."""
        bp = Breakpoint.from_pairs(
            (0.0, 5.0),
            ("50%", 10.0),
            ("99%", 2.0),
            name="test_bp"
        )

        self.assertEqual(len(bp), 3)
        self.assertEqual(bp.name, "test_bp")

    def test_linear_helper(self):
        """Test linear() helper method."""
        bp = Breakpoint.linear(0.0, 1.0, name="fade_up")

        self.assertEqual(len(bp), 2)
        self.assertEqual(bp.name, "fade_up")

    def test_fade_in_helper(self):
        """Test fade_in() helper method."""
        bp = Breakpoint.fade_in(duration_percent=10.0, max_value=1.0, name="fade_in")

        self.assertEqual(len(bp), 3)
        self.assertEqual(bp.name, "fade_in")

    def test_fade_out_helper(self):
        """Test fade_out() helper method."""
        bp = Breakpoint.fade_out(start_percent=90.0, start_value=1.0, name="fade_out")

        self.assertEqual(len(bp), 3)
        self.assertEqual(bp.name, "fade_out")


class TestBreakpointConversion(unittest.TestCase):
    """Test converting breakpoints to absolute times."""

    def test_percentage_conversion(self):
        """Test converting percentages to absolute times."""
        bp = Breakpoint()
        bp.add("0%", 5.0)
        bp.add("50%", 10.0)
        bp.add("99%", 2.0)

        duration = 2.0  # 2 seconds
        absolute = bp.to_absolute_times(duration)

        self.assertEqual(len(absolute), 3)
        self.assertAlmostEqual(absolute[0][0], 0.0)
        self.assertAlmostEqual(absolute[1][0], 1.0)
        self.assertAlmostEqual(absolute[2][0], 1.98)

    def test_sorting(self):
        """Test that breakpoints are sorted by time."""
        bp = Breakpoint()
        bp.add("99%", 2.0)
        bp.add("0%", 5.0)
        bp.add("50%", 10.0)

        duration = 2.0
        absolute = bp.to_absolute_times(duration)

        # Should be sorted: 0%, 50%, 99%
        self.assertLessEqual(absolute[0][0], absolute[1][0])
        self.assertLessEqual(absolute[1][0], absolute[2][0])


class TestBreakpointFileGeneration(unittest.TestCase):
    """Test generating breakpoint file content."""

    def test_file_content_format(self):
        """Test that file content has correct format."""
        bp = Breakpoint()
        bp.add("0%", 5.0)
        bp.add("50%", 10.0)
        bp.add("99%", 2.0)

        duration = 2.0
        content = bp.to_file_content(duration)

        lines = content.strip().split('\n')
        self.assertEqual(len(lines), 3)

        # Each line should have format: "time value"
        for line in lines:
            parts = line.split()
            self.assertEqual(len(parts), 2)
            # Should be able to parse as floats
            float(parts[0])
            float(parts[1])


class TestBreakpointWarnings(unittest.TestCase):
    """Test warnings for problematic breakpoint usage."""

    def test_beyond_duration_warning(self):
        """Test warning when absolute time is beyond file duration."""
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
            self.assertGreater(len(w), 0)
            self.assertIn("beyond file duration", str(w[0].message))

    def test_no_warning_for_percentages(self):
        """Test that no warning is issued for safe usage (all percentages)."""
        bp = Breakpoint()
        bp.add("0%", 0.0)
        bp.add("50%", 1.0)
        bp.add("100%", 0.0)

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = bp.to_absolute_times(0.3)

            # Should not have issued a warning
            self.assertEqual(len(w), 0)


class TestBreakpointIntegration(unittest.TestCase):
    """Test breakpoint integration with operations."""

    def test_breakpoint_with_operation(self):
        """Test creating operation with breakpoint parameter."""
        cyclecnt_bp = Breakpoint.from_pairs(
            ("0%", 5.0),
            ("50%", 10.0),
            ("100%", 2.0),
            name="cyclecnt"
        )

        # Create operation with breakpoint parameter
        distort_op = custom_operation(
            name="distort_average",
            program="distort",
            mode="average",
            mode_param=1,
            input_format=FileFormat.WAV,
            output_format=FileFormat.WAV,
            channels=ChannelMode.MONO,
            params=[cyclecnt_bp]
        )

        self.assertEqual(distort_op.program, "distort")
        self.assertEqual(distort_op.mode, "average")
        self.assertEqual(len(distort_op.params), 1)
        self.assertIsInstance(distort_op.params[0], Breakpoint)


if __name__ == "__main__":
    unittest.main()
