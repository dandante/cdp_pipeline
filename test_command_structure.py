#!/usr/bin/env python3

"""
Test to verify CDP command structure is built correctly.
"""

import unittest
from pathlib import Path

from cdp_pipeline import CDPOperation, AudioFile, FileFormat, ChannelMode, OperationRequirements
from cdp_pipeline.operations import custom_operation, blur, combine_interleave


class TestCommandStructure(unittest.TestCase):
    """Test CDP command structure building."""

    def test_simple_command(self):
        """Test a simple command without mode_param."""
        op = blur(2.0)

        input_file = AudioFile(Path("input.ana"), FileFormat.ANA, ChannelMode.MONO)
        output_file = AudioFile(Path("output.ana"), FileFormat.ANA, ChannelMode.MONO)

        args = op.get_command_args([input_file], output_file)

        expected = ["blur", "input.ana", "output.ana", "2.0"]
        self.assertEqual(args, expected)

    def test_multi_input_command(self):
        """Test multi-input command."""
        op = combine_interleave(leafsize=1)

        input_files = [
            AudioFile(Path("input1.ana"), FileFormat.ANA, ChannelMode.MONO),
            AudioFile(Path("input2.ana"), FileFormat.ANA, ChannelMode.MONO),
            AudioFile(Path("input3.ana"), FileFormat.ANA, ChannelMode.MONO),
        ]
        output_file = AudioFile(Path("output.ana"), FileFormat.ANA, ChannelMode.MONO)

        args = op.get_command_args(input_files, output_file)

        expected = ["interleave", "input1.ana", "input2.ana", "input3.ana", "output.ana", "1"]
        self.assertEqual(args, expected)

    def test_command_with_mode_param(self):
        """Test command with numeric mode parameter."""
        # Create the specfold operation
        # Command should be: specfold specfold 1 input.ana output.ana 1 4 3
        op = custom_operation(
            name="specfold_1",
            program="specfold",
            mode="specfold",
            mode_param=1,
            params=[1, 4, 3]
        )

        input_file = AudioFile(Path("input.ana"), FileFormat.ANA, ChannelMode.MONO)
        output_file = AudioFile(Path("output.ana"), FileFormat.ANA, ChannelMode.MONO)

        args = op.get_command_args([input_file], output_file)

        expected = ["specfold", "1", "input.ana", "output.ana", "1", "4", "3"]
        self.assertEqual(args, expected)

    def test_pvoc_anal_command(self):
        """Test pvoc anal command structure."""
        # Command should be: pvoc anal 1 input.wav output.ana
        op = custom_operation(
            name="pvoc_anal",
            program="pvoc",
            mode="anal",
            mode_param=1,
            input_format=FileFormat.WAV,
            output_format=FileFormat.ANA
        )

        input_file = AudioFile(Path("input.wav"), FileFormat.WAV, ChannelMode.MONO)
        output_file = AudioFile(Path("output.ana"), FileFormat.ANA, ChannelMode.MONO)

        args = op.get_command_args([input_file], output_file)

        expected = ["anal", "1", "input.wav", "output.ana"]
        self.assertEqual(args, expected)

    def test_command_with_only_params_after(self):
        """Test command with only params after files (no mode_param)."""
        op = custom_operation(
            name="test_op",
            program="testprog",
            mode="testmode",
            mode_param=None,
            params=[10, 20, 30]
        )

        input_file = AudioFile(Path("input.ana"), FileFormat.ANA, ChannelMode.MONO)
        output_file = AudioFile(Path("output.ana"), FileFormat.ANA, ChannelMode.MONO)

        args = op.get_command_args([input_file], output_file)

        expected = ["testmode", "input.ana", "output.ana", "10", "20", "30"]
        self.assertEqual(args, expected)


if __name__ == "__main__":
    unittest.main()
