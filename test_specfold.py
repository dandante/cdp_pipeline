#!/usr/bin/env python3

"""
Test script to verify specfold operation works correctly.
"""

import unittest
from pathlib import Path

from cdp_pipeline import Pipeline
from cdp_pipeline.operations import custom_operation
from cdp_pipeline.core import FileFormat, ChannelMode


class TestSpecfoldOperation(unittest.TestCase):
    """Test specfold operation."""

    def test_specfold_creation(self):
        """Test creating a specfold operation with correct parameters."""
        # Create the specfold operation
        # Command should be: specfold specfold 1 input.ana output.ana 1 4 3
        specfold_op = custom_operation(
            name="specfold_1",
            program="specfold",
            mode="specfold",
            mode_param=1,
            input_format=FileFormat.ANA,
            output_format=FileFormat.ANA,
            channels=ChannelMode.MONO,
            params=[1, 4, 3]
        )

        self.assertEqual(specfold_op.program, "specfold")
        self.assertEqual(specfold_op.mode, "specfold")
        self.assertEqual(specfold_op.mode_param, 1)
        self.assertEqual(specfold_op.params, [1, 4, 3])
        self.assertEqual(specfold_op.input_requirements.format, FileFormat.ANA)
        self.assertEqual(specfold_op.output_format, FileFormat.ANA)

    def test_specfold_pipeline_execution(self):
        """Test running specfold operation in pipeline with real file."""
        # Check if we have a test file
        test_file = Path("first_stereo.wav")
        if not test_file.exists():
            # Try to find any wav file
            wav_files = list(Path(".").glob("*.wav"))
            if not wav_files:
                self.skipTest("No WAV files found for integration test")
            test_file = wav_files[0]

        # Create the specfold operation
        specfold_op = custom_operation(
            name="specfold_1",
            program="specfold",
            mode="specfold",
            mode_param=1,
            input_format=FileFormat.ANA,
            output_format=FileFormat.ANA,
            channels=ChannelMode.MONO,
            params=[1, 4, 3]
        )

        # Create and run pipeline
        pipeline = Pipeline()
        pipeline.add_operation(specfold_op)

        output_file = "specfold_test_output.wav"

        try:
            result = pipeline.run(
                input_files=str(test_file),
                output_file=output_file,
                keep_temp=False,
                verbose=False,
                overwrite=True  # Allow overwriting existing output
            )

            # Verify output file was created
            self.assertTrue(result.path.exists())
            self.assertGreater(result.path.stat().st_size, 0)

            # Clean up output file
            if result.path.exists():
                result.path.unlink()

        except Exception as e:
            self.fail(f"Pipeline execution failed: {e}")


if __name__ == "__main__":
    unittest.main()
