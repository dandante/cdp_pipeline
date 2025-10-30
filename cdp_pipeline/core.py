"""
Core classes for CDP pipeline management.
"""

from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Union, Callable, Any


class FileFormat(Enum):
    """Supported file formats."""
    WAV = "wav"
    ANA = "ana"  # Spectral analysis format


class ChannelMode(Enum):
    """Channel configuration."""
    MONO = 1
    STEREO = 2


@dataclass
class AudioFile:
    """
    Represents an audio or analysis file with metadata.

    Attributes:
        path: File path
        format: File format (WAV or ANA)
        channels: Number of channels (MONO or STEREO)
        channel_index: For split stereo files, which channel (1 or 2)
    """
    path: Path
    format: FileFormat
    channels: ChannelMode
    channel_index: Optional[int] = None  # For split stereo: 1 (left) or 2 (right)

    def __post_init__(self):
        if isinstance(self.path, str):
            self.path = Path(self.path)
        if isinstance(self.format, str):
            self.format = FileFormat(self.format)
        if isinstance(self.channels, int):
            self.channels = ChannelMode(self.channels)

    @property
    def is_mono(self) -> bool:
        return self.channels == ChannelMode.MONO

    @property
    def is_stereo(self) -> bool:
        return self.channels == ChannelMode.STEREO

    @property
    def is_wav(self) -> bool:
        return self.format == FileFormat.WAV

    @property
    def is_ana(self) -> bool:
        return self.format == FileFormat.ANA

    def with_extension(self, ext: str) -> 'AudioFile':
        """Create a new AudioFile with a different extension."""
        new_path = self.path.with_suffix(f".{ext}")
        new_format = FileFormat.WAV if ext == "wav" else FileFormat.ANA
        return AudioFile(
            path=new_path,
            format=new_format,
            channels=self.channels,
            channel_index=self.channel_index
        )

    def with_suffix(self, suffix: str) -> 'AudioFile':
        """Create a new AudioFile with an added suffix before extension."""
        stem = self.path.stem
        ext = self.path.suffix
        new_path = self.path.with_name(f"{stem}{suffix}{ext}")
        return AudioFile(
            path=new_path,
            format=self.format,
            channels=self.channels,
            channel_index=self.channel_index
        )

    def __str__(self) -> str:
        channel_info = f"_c{self.channel_index}" if self.channel_index else ""
        return f"AudioFile({self.path.name}, {self.format.value}, {self.channels.name}{channel_info})"


@dataclass
class OperationRequirements:
    """
    Specifies what format and channel configuration an operation requires.
    """
    format: FileFormat
    channels: ChannelMode

    def __str__(self) -> str:
        return f"{self.format.value}/{self.channels.name}"


@dataclass
class CDPOperation:
    """
    Represents a CDP command/operation.

    Attributes:
        name: Human-readable operation name
        program: CDP program name (e.g., "combine", "blur")
        subcommand: CDP program subcommand (e.g., "interleave", "chorus")
        mode: Numeric mode parameter (comes after subcommand, before files)
        input_requirements: What format/channels the operation needs
        output_format: What format the operation produces
        params: Additional parameters for the operation (after files)
        multi_input: Whether operation takes multiple input files
    """
    name: str
    program: str
    subcommand: Optional[str] = None
    mode: Optional[Union[str, int]] = None  # Numeric mode after subcommand
    input_requirements: OperationRequirements = field(
        default_factory=lambda: OperationRequirements(FileFormat.ANA, ChannelMode.MONO)
    )
    output_format: FileFormat = FileFormat.ANA
    params: List[Any] = field(default_factory=list)
    multi_input: bool = False  # Whether this operation combines multiple inputs

    def get_command_args(self, input_files: List[AudioFile], output_file: AudioFile) -> List[str]:
        """
        Build the command arguments for this operation.

        Returns: List of command arguments (excluding program name)

        Command structure: program subcommand mode input(s) output params...
        Example: specfold specfold 1 input.ana output.ana 1 4 3
        """
        args = []

        # Add subcommand if present
        if self.subcommand:
            args.append(self.subcommand)

        # Add mode if present (comes after subcommand, before files)
        if self.mode is not None:
            args.append(str(self.mode))

        # Add input files
        if self.multi_input:
            args.extend([str(f.path) for f in input_files])
        else:
            args.append(str(input_files[0].path))

        # Add output file
        args.append(str(output_file.path))

        # Add parameters (come after files)
        args.extend([str(p) for p in self.params])

        return args

    def __str__(self) -> str:
        subcommand_str = f" {self.subcommand}" if self.subcommand else ""
        params_str = f" {self.params}" if self.params else ""
        return f"{self.program}{subcommand_str}{params_str}"
