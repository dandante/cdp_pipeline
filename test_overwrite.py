#!/usr/bin/env python3

"""
Test the overwrite flag functionality.
"""

import unittest
from pathlib import Path

from cdp_pipeline import Pipeline
from cdp_pipeline.operations import blur


class TestOverwriteFlag(unittest.TestCase):
    """Test overwrite flag behavior."""

    def test_overwrite_removes_existing_file(self):
        """Test that overwrite=True removes existing output file."""
        # Check if we have any wav files to test with
        wav_files = list(Path(".").glob("*.wav"))
        if not wav_files:
            self.skipTest("No WAV files found for integration test")

        input_file = wav_files[0]
        output_file = Path("test_overwrite_output.wav")

        # Create a dummy output file
        output_file.touch()
        self.assertTrue(output_file.exists())

        # Create and run pipeline with overwrite=True
        pipeline = Pipeline()
        pipeline.add_operation(blur(1.0))

        try:
            result = pipeline.run(
                input_files=str(input_file),
                output_file=output_file,
                overwrite=True,
                verbose=False
            )

            # Should succeed and create output
            self.assertTrue(result.path.exists())

        finally:
            # Clean up
            if output_file.exists():
                output_file.unlink()

    def test_without_overwrite_fails_on_existing_file(self):
        """Test that without overwrite flag, existing file causes failure."""
        # Check if we have any wav files to test with
        wav_files = list(Path(".").glob("*.wav"))
        if not wav_files:
            self.skipTest("No WAV files found for integration test")

        input_file = wav_files[0]
        output_file = Path("test_no_overwrite_output.wav")

        # Create output file first by running once
        pipeline = Pipeline()
        pipeline.add_operation(blur(1.0))

        try:
            # First run should succeed
            pipeline.run(
                input_files=str(input_file),
                output_file=output_file,
                overwrite=False,
                verbose=False
            )

            # Second run without overwrite should fail
            with self.assertRaises(Exception):
                pipeline.run(
                    input_files=str(input_file),
                    output_file=output_file,
                    overwrite=False,
                    verbose=False
                )

        finally:
            # Clean up
            if output_file.exists():
                output_file.unlink()


if __name__ == "__main__":
    unittest.main()
