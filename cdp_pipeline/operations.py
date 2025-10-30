"""
Pre-defined CDP operations and operation builders.
"""

from typing import Any, List, Optional
from .core import CDPOperation, FileFormat, ChannelMode, OperationRequirements


# ============================================================================
# Spectral Processing Operations (work on .ana files)
# ============================================================================

def blur(blur_amount: float = 1.0) -> CDPOperation:
    """
    Blur operation - spectral blurring.

    Args:
        blur_amount: Amount of blur to apply
    """
    return CDPOperation(
        name=f"blur_{blur_amount}",
        program="blur",
        subcommand="blur",
        input_requirements=OperationRequirements(FileFormat.ANA, ChannelMode.MONO),
        output_format=FileFormat.ANA,
        params=[blur_amount]
    )


def combine_interleave(leafsize: int = 1) -> CDPOperation:
    """
    Combine interleave operation - interleaves multiple spectral files.

    Args:
        leafsize: Leaf size parameter for interleaving
    """
    return CDPOperation(
        name=f"combine_interleave_{leafsize}",
        program="combine",
        subcommand="interleave",
        input_requirements=OperationRequirements(FileFormat.ANA, ChannelMode.MONO),
        output_format=FileFormat.ANA,
        params=[leafsize],
        multi_input=True
    )


def morph(morphing_factor: float = 0.5) -> CDPOperation:
    """
    Morph between two spectral files.

    Args:
        morphing_factor: Balance between inputs (0-1)
    """
    return CDPOperation(
        name=f"morph_{morphing_factor}",
        program="morph",
        subcommand="morph",
        input_requirements=OperationRequirements(FileFormat.ANA, ChannelMode.MONO),
        output_format=FileFormat.ANA,
        params=[morphing_factor],
        multi_input=True
    )


def pitch_transpose(semitones: float) -> CDPOperation:
    """
    Transpose pitch of spectral file.

    Args:
        semitones: Number of semitones to transpose
    """
    return CDPOperation(
        name=f"pitch_transpose_{semitones}",
        program="pitch",
        subcommand="transp",
        input_requirements=OperationRequirements(FileFormat.ANA, ChannelMode.MONO),
        output_format=FileFormat.ANA,
        params=[semitones]
    )


def stretch_time(time_stretch: float) -> CDPOperation:
    """
    Time-stretch spectral file without changing pitch.

    Args:
        time_stretch: Stretch factor (2.0 = twice as long)
    """
    return CDPOperation(
        name=f"stretch_time_{time_stretch}",
        program="stretch",
        subcommand="time",
        input_requirements=OperationRequirements(FileFormat.ANA, ChannelMode.MONO),
        output_format=FileFormat.ANA,
        params=[time_stretch]
    )


# ============================================================================
# Time Domain Operations (work on .wav files)
# ============================================================================

def modify_speed(speed: float) -> CDPOperation:
    """
    Change speed of audio file (affects both pitch and duration).

    Uses mode 1: Vary speed/pitch of a sound.

    Args:
        speed: Speed multiplier (2.0 = twice as fast)
    """
    return CDPOperation(
        name=f"modify_speed_{speed}",
        program="modify",
        subcommand="speed",
        mode=1,  # Mode 1: Vary speed/pitch
        input_requirements=OperationRequirements(FileFormat.WAV, ChannelMode.MONO),
        output_format=FileFormat.WAV,
        params=[speed]
    )


def envel_attack(attack_time: float) -> CDPOperation:
    """
    Apply attack envelope to audio.

    Args:
        attack_time: Attack time in seconds
    """
    return CDPOperation(
        name=f"envel_attack_{attack_time}",
        program="envel",
        subcommand="attack",
        input_requirements=OperationRequirements(FileFormat.WAV, ChannelMode.MONO),
        output_format=FileFormat.WAV,
        params=[attack_time]
    )


def filter_lohi(attenuation: float, pass_band: float, stop_band: float, mode: int = 1) -> CDPOperation:
    """
    Apply low-pass or high-pass filter using filter lohi.

    If stop_band > pass_band: low-pass filter
    If stop_band < pass_band: high-pass filter

    Args:
        attenuation: Gain reduction in dB (0 to -96). Greater attenuation = sharper filter.
        pass_band: Last pitch to be passed by the filter (Hz if mode=1, MIDI if mode=2)
        stop_band: First pitch to be stopped by the filter (Hz if mode=1, MIDI if mode=2)
        mode: 1 = frequencies in Hz, 2 = MIDI note values
    """
    return CDPOperation(
        name=f"filter_lohi_{pass_band}_{stop_band}",
        program="filter",
        subcommand="lohi",
        mode=mode,
        input_requirements=OperationRequirements(FileFormat.WAV, ChannelMode.MONO),
        output_format=FileFormat.WAV,
        params=[attenuation, pass_band, stop_band]
    )


# ============================================================================
# Custom Operations
# ============================================================================

def custom_operation(
    name: str,
    program: str,
    subcommand: Optional[str] = None,
    mode: Optional[Any] = None,
    input_format: FileFormat = FileFormat.ANA,
    output_format: FileFormat = FileFormat.ANA,
    channels: ChannelMode = ChannelMode.MONO,
    params: Optional[List[Any]] = None,
    multi_input: bool = False
) -> CDPOperation:
    """
    Create a custom CDP operation.

    Args:
        name: Human-readable name
        program: CDP program name
        subcommand: CDP program subcommand
        mode: Numeric mode parameter (comes after subcommand, before files)
        input_format: Required input format
        output_format: Produced output format
        channels: Required channel configuration
        params: Additional parameters (come after files)
        multi_input: Whether operation takes multiple inputs

    Example:
        # For: specfold specfold 1 input.ana output.ana 1 4 3
        custom_operation(
            name="specfold_1",
            program="specfold",
            subcommand="specfold",
            mode=1,
            params=[1, 4, 3]
        )
    """
    return CDPOperation(
        name=name,
        program=program,
        subcommand=subcommand,
        mode=mode,
        input_requirements=OperationRequirements(input_format, channels),
        output_format=output_format,
        params=params or [],
        multi_input=multi_input
    )


# ============================================================================
# Operation Groups (for common workflows)
# ============================================================================

def get_spectral_operations() -> List[str]:
    """Get list of available spectral operations."""
    return [
        "blur", "combine_interleave", "morph", "pitch_transpose", "stretch_time"
    ]


def get_time_domain_operations() -> List[str]:
    """Get list of available time domain operations."""
    return [
        "modify_speed", "envel_attack", "filter_lohi"
    ]
