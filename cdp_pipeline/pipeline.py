"""
Pipeline composition for chaining CDP operations.
"""

import shutil
from pathlib import Path
from typing import List, Optional, Union
from .core import AudioFile, FileFormat, ChannelMode, CDPOperation
from .executor import PipelineExecutor


class Pipeline:
    """
    A pipeline of CDP operations that can be applied to audio files.

    Example:
        pipeline = Pipeline()
        pipeline.add_operation(blur(2.0))
        pipeline.add_operation(pitch_transpose(3.5))
        pipeline.run(input_files, output_file)
    """

    def __init__(self, operations: Optional[List[CDPOperation]] = None):
        """
        Initialize a pipeline.

        Args:
            operations: Initial list of operations (optional)
        """
        self.operations = operations or []

    def add_operation(self, operation: CDPOperation) -> 'Pipeline':
        """
        Add an operation to the pipeline.

        Args:
            operation: The operation to add

        Returns: self for chaining
        """
        self.operations.append(operation)
        return self

    def run(
        self,
        input_files: Union[str, Path, List[Union[str, Path]]],
        output_file: Union[str, Path],
        temp_dir: Optional[Path] = None,
        keep_temp: bool = False,
        output_channels: Optional[ChannelMode] = None,
        output_format: Optional[FileFormat] = None,
        verbose: bool = False,
        overwrite: bool = False
    ) -> AudioFile:
        """
        Execute the pipeline.

        Args:
            input_files: Input file(s)
            output_file: Output file path
            temp_dir: Temporary directory (None = auto)
            keep_temp: Keep temporary files after execution
            output_channels: Desired output channel mode (None = preserve input)
            output_format: Desired output format (None = WAV)
            verbose: If True, print CDP commands as they are executed
            overwrite: If True, remove output file if it exists before running

        Returns: AudioFile for the output
        """
        # Normalize inputs
        if not isinstance(input_files, list):
            input_files = [input_files]

        output_path = Path(output_file)
        output_format = output_format or FileFormat.WAV

        # Handle overwrite
        if overwrite and output_path.exists():
            output_path.unlink()

        # Create executor
        with PipelineExecutor(temp_dir=temp_dir, keep_temp=keep_temp, verbose=verbose) as executor:
            # Load input files
            audio_files = []
            for input_file in input_files:
                input_path = Path(input_file)
                if not input_path.exists():
                    raise FileNotFoundError(f"Input file not found: {input_path}")

                fmt, channels = executor.get_file_info(input_path)
                audio_files.append(AudioFile(
                    path=input_path,
                    format=fmt,
                    channels=channels
                ))

            # Determine if input is stereo
            input_is_stereo = any(f.is_stereo for f in audio_files)

            # Execute each operation in sequence
            current_files = audio_files
            for i, operation in enumerate(self.operations):
                operation_name = f"op{i:02d}_{operation.name}"
                current_files = executor.execute_operation(
                    operation,
                    current_files,
                    output_base_name=operation_name
                )

            # Convert output to desired format
            if output_format == FileFormat.WAV:
                current_files = [executor.convert_to_wav(f) for f in current_files]
            elif output_format == FileFormat.ANA:
                current_files = [executor.convert_to_ana(f) for f in current_files]

            # Handle channel configuration for output
            if output_channels == ChannelMode.STEREO or (output_channels is None and input_is_stereo):
                # Need stereo output
                if len(current_files) == 2:
                    # We have left and right channels
                    left = next((f for f in current_files if f.channel_index == 1), current_files[0])
                    right = next((f for f in current_files if f.channel_index == 2), current_files[1])

                    # Ensure both are WAV
                    if not left.is_wav:
                        left = executor.convert_to_wav(left)
                    if not right.is_wav:
                        right = executor.convert_to_wav(right)

                    # Merge to stereo
                    result = executor.merge_stereo(left, right, output_path)
                elif len(current_files) == 1 and current_files[0].is_stereo:
                    # Already stereo
                    result = current_files[0]
                    shutil.copy(result.path, output_path)
                    result.path = output_path
                else:
                    raise ValueError(f"Cannot create stereo output from {len(current_files)} mono file(s)")
            else:
                # Mono output or multiple outputs
                if len(current_files) == 1:
                    result = current_files[0]
                    shutil.copy(result.path, output_path)
                    result.path = output_path
                else:
                    # Multiple outputs - just take the first or raise error?
                    raise ValueError(
                        f"Pipeline produced {len(current_files)} outputs. "
                        "Specify output_channels or provide a single-output pipeline."
                    )

            return result

    def __len__(self) -> int:
        """Return number of operations in pipeline."""
        return len(self.operations)

    def __str__(self) -> str:
        """String representation of pipeline."""
        if not self.operations:
            return "Pipeline(empty)"

        ops_str = " -> ".join(str(op) for op in self.operations)
        return f"Pipeline({ops_str})"


class PipelineBuilder:
    """
    Fluent interface for building pipelines.

    Example:
        result = (PipelineBuilder(input_files)
                  .blur(2.0)
                  .pitch_transpose(3.5)
                  .output("result.wav"))
    """

    def __init__(self, input_files: Union[str, Path, List[Union[str, Path]]]):
        """
        Initialize builder with input files.

        Args:
            input_files: Input file(s)
        """
        self.input_files = input_files
        self.pipeline = Pipeline()

    def add(self, operation: CDPOperation) -> 'PipelineBuilder':
        """
        Add a custom operation.

        Args:
            operation: Operation to add

        Returns: self for chaining
        """
        self.pipeline.add_operation(operation)
        return self

    def output(
        self,
        output_file: Union[str, Path],
        temp_dir: Optional[Path] = None,
        keep_temp: bool = False,
        output_channels: Optional[ChannelMode] = None,
        output_format: Optional[FileFormat] = None,
        verbose: bool = False,
        overwrite: bool = False
    ) -> AudioFile:
        """
        Execute pipeline and write output.

        Args:
            output_file: Output file path
            temp_dir: Temporary directory (None = auto)
            keep_temp: Keep temporary files
            output_channels: Desired output channel mode
            output_format: Desired output format
            verbose: If True, print CDP commands as they are executed
            overwrite: If True, remove output file if it exists before running

        Returns: AudioFile for the output
        """
        return self.pipeline.run(
            self.input_files,
            output_file,
            temp_dir=temp_dir,
            keep_temp=keep_temp,
            output_channels=output_channels,
            output_format=output_format,
            verbose=verbose,
            overwrite=overwrite
        )

    def __str__(self) -> str:
        return f"PipelineBuilder({self.pipeline})"
