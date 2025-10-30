#!/usr/bin/env python3

"""
Basic tests to verify the cdp_pipeline library works.
"""

import unittest
from pathlib import Path

from cdp_pipeline import Pipeline, PipelineBuilder, AudioFile, FileFormat, ChannelMode
from cdp_pipeline.operations import blur, combine_interleave, pitch_transpose
from cdp_pipeline.executor import PipelineExecutor


class TestAudioFile(unittest.TestCase):
    """Test AudioFile class."""

    def test_audio_file_properties(self):
        """Test AudioFile properties."""
        af = AudioFile(
            path="test.wav",
            format=FileFormat.WAV,
            channels=ChannelMode.MONO
        )

        self.assertTrue(af.is_wav)
        self.assertFalse(af.is_ana)
        self.assertTrue(af.is_mono)
        self.assertFalse(af.is_stereo)

    def test_with_extension(self):
        """Test AudioFile.with_extension() method."""
        af = AudioFile(
            path="test.wav",
            format=FileFormat.WAV,
            channels=ChannelMode.MONO
        )

        ana_file = af.with_extension("ana")
        self.assertTrue(ana_file.is_ana)
        self.assertEqual(ana_file.path.suffix, ".ana")

    def test_with_suffix(self):
        """Test AudioFile.with_suffix() method."""
        af = AudioFile(
            path="test.wav",
            format=FileFormat.WAV,
            channels=ChannelMode.MONO
        )

        suffixed = af.with_suffix("_processed")
        self.assertIn("_processed", str(suffixed.path))


class TestOperations(unittest.TestCase):
    """Test operation creation."""

    def test_blur_operation(self):
        """Test blur operation creation."""
        blur_op = blur(2.0)
        self.assertEqual(blur_op.program, "blur")
        self.assertEqual(blur_op.subcommand, "blur")
        self.assertEqual(blur_op.input_requirements.format, FileFormat.ANA)
        self.assertIn(2.0, blur_op.params)

    def test_combine_interleave_operation(self):
        """Test combine interleave operation creation."""
        interleave_op = combine_interleave(leafsize=3)
        self.assertEqual(interleave_op.program, "combine")
        self.assertTrue(interleave_op.multi_input)
        self.assertIn(3, interleave_op.params)


class TestPipeline(unittest.TestCase):
    """Test Pipeline class."""

    def test_pipeline_creation(self):
        """Test pipeline creation and composition."""
        pipeline = Pipeline()
        self.assertEqual(len(pipeline), 0)

        pipeline.add_operation(blur(1.5))
        pipeline.add_operation(pitch_transpose(3.0))
        self.assertEqual(len(pipeline), 2)

    def test_pipeline_builder(self):
        """Test PipelineBuilder."""
        builder = PipelineBuilder(["input1.wav", "input2.wav"])
        builder.add(blur(2.0))
        builder.add(pitch_transpose(-5.0))

        self.assertEqual(len(builder.pipeline), 2)


class TestExecutor(unittest.TestCase):
    """Test PipelineExecutor."""

    def test_executor_initialization(self):
        """Test PipelineExecutor initialization."""
        with PipelineExecutor(keep_temp=True) as executor:
            self.assertTrue(executor.temp_dir.exists())

    def test_real_file_info(self):
        """Test getting file info from real files if they exist."""
        # Check if we have any wav files to test with
        wav_files = list(Path(".").glob("*.wav"))

        if not wav_files:
            self.skipTest("No WAV files found in current directory")

        test_file = wav_files[0]

        with PipelineExecutor() as executor:
            fmt, channels = executor.get_file_info(test_file)
            self.assertIn(fmt, [FileFormat.WAV, FileFormat.ANA])
            self.assertIn(channels, [ChannelMode.MONO, ChannelMode.STEREO])

            af = AudioFile(path=test_file, format=fmt, channels=channels)
            self.assertEqual(af.path, test_file)


if __name__ == "__main__":
    unittest.main()
