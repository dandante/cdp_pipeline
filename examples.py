#!/usr/bin/env python3

"""
Examples demonstrating the cdp_pipeline library usage.
"""

from cdp_pipeline import Pipeline, PipelineBuilder
from cdp_pipeline.operations import (
    blur, combine_interleave, morph, pitch_transpose, stretch,
    custom_operation
)
from cdp_pipeline.core import FileFormat, ChannelMode


def example1_simple_blur():
    """
    Example 1: Apply spectral blur to a single file.

    The library automatically:
    - Converts WAV to ANA
    - Applies blur
    - Converts back to WAV
    """
    print("Example 1: Simple blur")

    pipeline = Pipeline()
    pipeline.add_operation(blur(blur_amount=2.0))

    result = pipeline.run(
        input_files="input.wav",
        output_file="blurred.wav"
    )

    print(f"Created: {result.path}\n")


def example2_chained_operations():
    """
    Example 2: Chain multiple operations.

    Apply blur, then transpose pitch, then time-stretch.
    """
    print("Example 2: Chained operations")

    pipeline = Pipeline()
    pipeline.add_operation(blur(1.5))
    pipeline.add_operation(pitch_transpose(semitones=5.0))
    pipeline.add_operation(stretch(time_stretch=1.5))

    result = pipeline.run(
        input_files="input.wav",
        output_file="processed.wav"
    )

    print(f"Created: {result.path}\n")


def example3_combine_multiple_files():
    """
    Example 3: Combine multiple files with interleave.

    Works with both mono and stereo files.
    For stereo files, each channel is processed separately then re-merged.
    """
    print("Example 3: Interleave multiple files")

    pipeline = Pipeline()
    pipeline.add_operation(combine_interleave(leafsize=1))

    result = pipeline.run(
        input_files=["file1.wav", "file2.wav", "file3.wav"],
        output_file="interleaved.wav"
    )

    print(f"Created: {result.path}\n")


def example4_morph_between_sounds():
    """
    Example 4: Morph between two sounds.

    Morphing factor 0.5 = equal blend
    0.0 = all first file, 1.0 = all second file
    """
    print("Example 4: Morph between two sounds")

    pipeline = Pipeline()
    pipeline.add_operation(morph(morphing_factor=0.5))

    result = pipeline.run(
        input_files=["sound1.wav", "sound2.wav"],
        output_file="morphed.wav"
    )

    print(f"Created: {result.path}\n")


def example5_pipeline_builder():
    """
    Example 5: Using PipelineBuilder for fluent API.

    This provides a more concise syntax for simple pipelines.
    """
    print("Example 5: Using PipelineBuilder")

    result = (PipelineBuilder(["input1.wav", "input2.wav"])
              .add(combine_interleave(leafsize=2))
              .add(blur(1.5))
              .add(pitch_transpose(-3.0))
              .output("result.wav"))

    print(f"Created: {result.path}\n")


def example6_custom_operation():
    """
    Example 6: Define a custom CDP operation.

    For operations not predefined in the operations module.
    Demonstrates proper use of mode_param for commands with numeric modes.
    """
    print("Example 6: Custom operation")

    # Create a custom operation for CDP's "specfold" program
    # Command structure: specfold specfold 1 input.ana output.ana 1 4 3
    # - program: specfold
    # - mode: specfold (subcommand)
    # - mode_param: 1 (numeric mode, comes after mode but before files)
    # - params: [1, 4, 3] (come after files)
    specfold_op = custom_operation(
        name="specfold_1",
        program="specfold",
        mode="specfold",
        mode_param=1,  # Numeric mode goes here
        input_format=FileFormat.ANA,
        output_format=FileFormat.ANA,
        channels=ChannelMode.MONO,
        params=[1, 4, 3]  # Parameters after files
    )

    pipeline = Pipeline()
    pipeline.add_operation(specfold_op)

    result = pipeline.run(
        input_files="input.wav",
        output_file="specfolded.wav"
    )

    print(f"Created: {result.path}\n")


def example7_keep_temporary_files():
    """
    Example 7: Keep temporary files for debugging.

    Useful for inspecting intermediate results.
    """
    print("Example 7: Keep temporary files")

    pipeline = Pipeline()
    pipeline.add_operation(blur(2.0))
    pipeline.add_operation(stretch(2.0))

    result = pipeline.run(
        input_files="input.wav",
        output_file="stretched_blur.wav",
        temp_dir="./debug_temp",  # Specify temp directory
        keep_temp=True  # Don't delete temp files
    )

    print(f"Created: {result.path}")
    print("Temporary files kept in ./debug_temp/\n")


def example8_stereo_to_mono_processing():
    """
    Example 8: Process stereo files.

    Stereo files are automatically split, processed per-channel,
    then merged back to stereo.
    """
    print("Example 8: Stereo file processing")

    pipeline = Pipeline()
    pipeline.add_operation(blur(3.0))
    pipeline.add_operation(pitch_transpose(7.0))

    # Input is stereo, output will be stereo
    result = pipeline.run(
        input_files="stereo_input.wav",
        output_file="stereo_output.wav"
    )

    print(f"Created: {result.path} (stereo)\n")


def example9_complex_interleave_workflow():
    """
    Example 9: Complex workflow - the original interleave.py use case.

    Take multiple stereo files, interleave them, apply processing.
    """
    print("Example 9: Complex interleave workflow")

    # This is equivalent to the original interleave.py but much simpler
    pipeline = Pipeline()
    pipeline.add_operation(combine_interleave(leafsize=1))
    pipeline.add_operation(blur(1.2))
    pipeline.add_operation(stretch(1.3))

    result = pipeline.run(
        input_files=["stereo1.wav", "stereo2.wav", "stereo3.wav"],
        output_file="complex_result.wav",
        keep_temp=False
    )

    print(f"Created: {result.path}\n")


def example10_output_formats():
    """
    Example 10: Control output format.

    You can output to ANA format if needed for further spectral processing.
    """
    print("Example 10: Output to ANA format")

    pipeline = Pipeline()
    pipeline.add_operation(blur(2.0))

    # Output as ANA file
    result = pipeline.run(
        input_files="input.wav",
        output_file="blurred.ana",
        output_format=FileFormat.ANA
    )

    print(f"Created: {result.path} (analysis format)\n")


if __name__ == "__main__":
    print("CDP Pipeline Library - Usage Examples")
    print("=" * 50)
    print()

    # Note: These examples assume the input files exist.
    # Uncomment the examples you want to run:

    # example1_simple_blur()
    # example2_chained_operations()
    # example3_combine_multiple_files()
    # example4_morph_between_sounds()
    # example5_pipeline_builder()
    # example6_custom_operation()
    # example7_keep_temporary_files()
    # example8_stereo_to_mono_processing()
    # example9_complex_interleave_workflow()
    # example10_output_formats()

    print("\nUncomment the examples you want to run!")
    print("Make sure the input files exist before running.")
