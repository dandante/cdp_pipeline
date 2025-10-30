"""
Execution engine for CDP pipelines.
"""

import os
import shutil
import tempfile
from pathlib import Path
from typing import List, Optional, Dict, Tuple, Any
import sh

from .core import AudioFile, FileFormat, ChannelMode, CDPOperation
from .breakpoint import Breakpoint, is_automatable


class PipelineExecutor:
    """
    Manages execution of CDP operations with automatic format conversion.
    """

    def __init__(self, temp_dir: Optional[Path] = None, keep_temp: bool = False, verbose: bool = False):
        """
        Initialize executor.

        Args:
            temp_dir: Temporary directory for intermediate files (None = auto)
            keep_temp: If True, don't delete temp files after execution
            verbose: If True, print CDP commands before executing them
        """
        self.keep_temp = keep_temp
        self.verbose = verbose
        self._temp_dir_obj = None
        self._counter = 0

        if temp_dir:
            self.temp_dir = Path(temp_dir)
            self.temp_dir.mkdir(parents=True, exist_ok=True)
        else:
            self._temp_dir_obj = tempfile.TemporaryDirectory()
            self.temp_dir = Path(self._temp_dir_obj.name)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

    def cleanup(self):
        """Clean up temporary files."""
        if not self.keep_temp and self._temp_dir_obj:
            self._temp_dir_obj.cleanup()
        elif not self.keep_temp:
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _next_temp_file(self, base_name: str, extension: str) -> Path:
        """Generate a unique temporary file path."""
        self._counter += 1
        return self.temp_dir / f"{base_name}_{self._counter:04d}.{extension}"

    def get_file_info(self, path: Path) -> Tuple[FileFormat, ChannelMode]:
        """
        Get format and channel info for a file.

        Returns: (format, channels)
        """
        # Determine format from extension
        if path.suffix == ".ana":
            fmt = FileFormat.ANA
        elif path.suffix == ".wav":
            fmt = FileFormat.WAV
        else:
            raise ValueError(f"Unknown file format: {path.suffix}")

        # Get channel count for WAV files
        if fmt == FileFormat.WAV:
            try:
                channel_count = int(sh.sfprops("-c", str(path)))
                channels = ChannelMode(channel_count)
            except Exception as e:
                raise RuntimeError(f"Failed to get channel info for {path}: {e}")
        else:
            # For .ana files, we need to track this separately
            # For now, assume mono unless specified
            channels = ChannelMode.MONO

        return fmt, channels

    def get_duration(self, audio_file: AudioFile) -> float:
        """
        Get the duration of an audio file in seconds.

        Args:
            audio_file: AudioFile to get duration for

        Returns: Duration in seconds
        """
        try:
            # Use sndinfo len to get duration
            # Output format: "DURATION: X.XXXXXX secs samples NNNNNN"
            result = str(sh.sndinfo("len", str(audio_file.path)))

            # Parse duration from output
            # Look for line like "DURATION: 1.917333 secs samples 184064"
            for line in result.split('\n'):
                if 'DURATION:' in line:
                    # Extract the number after "DURATION:"
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == 'DURATION:' and i + 1 < len(parts):
                            return float(parts[i + 1])

            raise RuntimeError(f"Could not parse duration from sndinfo output: {result}")

        except Exception as e:
            raise RuntimeError(f"Failed to get duration for {audio_file.path}: {e}")

    def write_breakpoint_file(self, breakpoint: Breakpoint, duration: float, base_name: str = "breakpoint") -> Path:
        """
        Write a breakpoint to a temporary file.

        Args:
            breakpoint: Breakpoint to write
            duration: Duration of the audio file (for percentage calculations)
            base_name: Base name for the temp file

        Returns: Path to the written breakpoint file
        """
        filepath = self._next_temp_file(base_name, "txt")
        breakpoint.write_to_file(filepath, duration)

        if self.verbose:
            print(f"Created breakpoint file: {filepath}")
            content = filepath.read_text()
            print(f"  Content:\n{content}")

        return filepath

    def split_stereo(self, audio_file: AudioFile) -> List[AudioFile]:
        """
        Split a stereo file into mono channels.

        Returns: List of [left_channel, right_channel] AudioFiles
        """
        if not audio_file.is_stereo:
            return [audio_file]

        # Copy to temp directory first
        temp_input = self.temp_dir / audio_file.path.name
        shutil.copy(audio_file.path, temp_input)

        # Split using housekeep chans
        sh.housekeep("chans", "2", str(temp_input))

        # Create AudioFile objects for each channel
        channels = []
        for i in range(1, 3):
            channel_path = temp_input.parent / temp_input.name.replace(".wav", f"_c{i}.wav")
            channels.append(AudioFile(
                path=channel_path,
                format=FileFormat.WAV,
                channels=ChannelMode.MONO,
                channel_index=i
            ))

        return channels

    def merge_stereo(self, left: AudioFile, right: AudioFile, output_path: Path) -> AudioFile:
        """
        Merge two mono files into a stereo file.

        Args:
            left: Left channel file
            right: Right channel file
            output_path: Output path for stereo file

        Returns: AudioFile for the merged stereo file
        """
        if not left.is_mono or not right.is_mono:
            raise ValueError("Both inputs must be mono files")

        if not left.is_wav or not right.is_wav:
            raise ValueError("Both inputs must be WAV files")

        # Use submix to merge
        sh.submix("interleave", str(left.path), str(right.path), str(output_path))

        return AudioFile(
            path=output_path,
            format=FileFormat.WAV,
            channels=ChannelMode.STEREO
        )

    def convert_to_ana(self, audio_file: AudioFile, window_size: int = 2048) -> AudioFile:
        """
        Convert WAV to analysis format.

        Args:
            audio_file: Input WAV file
            window_size: FFT window size

        Returns: AudioFile for the .ana file
        """
        if not audio_file.is_wav:
            return audio_file

        output_path = self._next_temp_file(audio_file.path.stem, "ana")

        # Use pvoc anal
        sh.pvoc("anal", "1", str(audio_file.path), str(output_path))

        return AudioFile(
            path=output_path,
            format=FileFormat.ANA,
            channels=audio_file.channels,
            channel_index=audio_file.channel_index
        )

    def convert_to_wav(self, audio_file: AudioFile) -> AudioFile:
        """
        Convert analysis format to WAV.

        Args:
            audio_file: Input .ana file

        Returns: AudioFile for the WAV file
        """
        if not audio_file.is_ana:
            return audio_file

        output_path = self._next_temp_file(audio_file.path.stem, "wav")

        # Use pvoc synth
        sh.pvoc("synth", str(audio_file.path), str(output_path))

        return AudioFile(
            path=output_path,
            format=FileFormat.WAV,
            channels=audio_file.channels,
            channel_index=audio_file.channel_index
        )

    def prepare_inputs(
        self,
        input_files: List[AudioFile],
        required_format: FileFormat,
        required_channels: ChannelMode
    ) -> List[AudioFile]:
        """
        Prepare input files for an operation by converting to required format/channels.

        Args:
            input_files: Input files
            required_format: Required format (WAV or ANA)
            required_channels: Required channel mode (MONO or STEREO)

        Returns: List of prepared AudioFiles
        """
        prepared = []

        for audio_file in input_files:
            # Handle channel conversion
            if required_channels == ChannelMode.MONO and audio_file.is_stereo:
                # Split stereo to mono - this returns list of channels
                mono_files = self.split_stereo(audio_file)
                prepared.extend(mono_files)
            elif required_channels == ChannelMode.STEREO and audio_file.is_mono:
                # Can't make stereo from single mono file
                raise ValueError(f"Cannot convert mono file {audio_file} to stereo")
            else:
                prepared.append(audio_file)

        # Handle format conversion
        converted = []
        for audio_file in prepared:
            if required_format == FileFormat.ANA and audio_file.is_wav:
                converted.append(self.convert_to_ana(audio_file))
            elif required_format == FileFormat.WAV and audio_file.is_ana:
                converted.append(self.convert_to_wav(audio_file))
            else:
                converted.append(audio_file)

        return converted

    def execute_operation(
        self,
        operation: CDPOperation,
        input_files: List[AudioFile],
        output_base_name: str = "output"
    ) -> List[AudioFile]:
        """
        Execute a single CDP operation.

        Args:
            operation: The operation to execute
            input_files: Input files
            output_base_name: Base name for output files

        Returns: List of output AudioFiles
        """
        # Prepare inputs
        prepared_inputs = self.prepare_inputs(
            input_files,
            operation.input_requirements.format,
            operation.input_requirements.channels
        )

        # If operation requires mono and we have stereo input, we'll have multiple channels
        # We need to process each channel separately
        if operation.input_requirements.channels == ChannelMode.MONO:
            # Group by channel
            channels: Dict[Optional[int], List[AudioFile]] = {}
            for f in prepared_inputs:
                if f.channel_index not in channels:
                    channels[f.channel_index] = []
                channels[f.channel_index].append(f)

            # Process each channel
            output_files = []
            for channel_idx, channel_files in channels.items():
                # Create output file
                suffix = f"_c{channel_idx}" if channel_idx else ""
                output_path = self._next_temp_file(
                    f"{output_base_name}{suffix}",
                    operation.output_format.value
                )

                output_file = AudioFile(
                    path=output_path,
                    format=operation.output_format,
                    channels=ChannelMode.MONO,
                    channel_index=channel_idx
                )

                # Process breakpoint parameters
                processed_operation = self._process_breakpoints(operation, channel_files)

                # Build and execute command
                cmd_args = processed_operation.get_command_args(channel_files, output_file)
                self._execute_cdp_command(processed_operation.program, cmd_args)

                output_files.append(output_file)

            return output_files
        else:
            # Process as single operation
            output_path = self._next_temp_file(
                output_base_name,
                operation.output_format.value
            )

            output_file = AudioFile(
                path=output_path,
                format=operation.output_format,
                channels=operation.input_requirements.channels
            )

            # Process breakpoint parameters
            processed_operation = self._process_breakpoints(operation, prepared_inputs)

            cmd_args = processed_operation.get_command_args(prepared_inputs, output_file)
            self._execute_cdp_command(processed_operation.program, cmd_args)

            return [output_file]

    def _process_breakpoints(self, operation: CDPOperation, input_files: List[AudioFile]) -> CDPOperation:
        """
        Process breakpoint parameters in an operation.

        If the operation has any Breakpoint parameters, this method:
        1. Gets the duration of the first input file
        2. Writes breakpoint files to temp directory
        3. Returns a copy of the operation with file paths instead of Breakpoints

        Args:
            operation: The operation to process
            input_files: Input files (used to get duration)

        Returns: Operation with breakpoints replaced by file paths
        """
        # Check if operation has any breakpoint parameters
        has_breakpoints = any(is_automatable(p) for p in operation.params)

        if not has_breakpoints:
            return operation

        # Get duration from first input file
        duration = self.get_duration(input_files[0])

        # Process parameters, replacing Breakpoints with file paths
        processed_params = []
        for i, param in enumerate(operation.params):
            if is_automatable(param):
                # Write breakpoint to file
                bp_file = self.write_breakpoint_file(
                    param,
                    duration,
                    base_name=f"{operation.name}_param{i}"
                )
                processed_params.append(str(bp_file))
            else:
                processed_params.append(param)

        # Create a new operation with processed params
        # We need to import dataclasses.replace or create a new instance
        from dataclasses import replace
        return replace(operation, params=processed_params)

    def _execute_cdp_command(self, program: str, args: List[str]):
        """Execute a CDP command."""
        if self.verbose:
            print(f"Executing: {program} {' '.join(str(a) for a in args)}")

        try:
            cdp_command = getattr(sh, program)
            result = cdp_command(*args)
            return result
        except Exception as e:
            raise RuntimeError(f"CDP command failed: {program} {' '.join(args)}\nError: {e}")
