"""
Breakpoint automation for time-varying parameters in CDP.

CDP supports breakpoint files for parameters that can vary over time.
See: https://www.composersdesktop.com/docs/charts/glosstec.htm#BREAKPOINT
"""

from typing import List, Tuple, Union, Optional
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class BreakpointValue:
    """
    A single breakpoint (time, value) pair.

    time can be either:
    - A float representing seconds (e.g., 1.5)
    - A string percentage (e.g., "50%")
    """
    time: Union[float, str]
    value: float

    def is_percentage(self) -> bool:
        """Check if time is specified as a percentage."""
        return isinstance(self.time, str) and self.time.endswith('%')

    def get_absolute_time(self, duration: float) -> float:
        """
        Convert time to absolute seconds.

        Args:
            duration: Total duration of the audio file in seconds

        Returns: Absolute time in seconds
        """
        if self.is_percentage():
            percentage = float(self.time.rstrip('%'))
            return (percentage / 100.0) * duration
        else:
            return float(self.time)


@dataclass
class Breakpoint:
    """
    Represents a breakpoint automation curve for time-varying parameters.

    CDP breakpoint files contain pairs of numbers (time value) on each line.
    Times must be in ascending order.

    Example:
        # Fade in from 0 to 1 over first half, then stay at 1
        bp = Breakpoint()
        bp.add(0.0, 0.0)
        bp.add("50%", 1.0)
        bp.add("100%", 1.0)

    See: https://www.composersdesktop.com/docs/charts/glosstec.htm#BREAKPOINT
    """

    points: List[BreakpointValue] = field(default_factory=list)
    name: Optional[str] = None  # Optional name for debugging

    def add(self, time: Union[float, str], value: float) -> 'Breakpoint':
        """
        Add a breakpoint.

        Args:
            time: Time in seconds (float) or percentage (string like "50%")
            value: Value at that time

        Returns: self for chaining
        """
        self.points.append(BreakpointValue(time, value))
        return self

    def to_absolute_times(self, duration: float) -> List[Tuple[float, float]]:
        """
        Convert all breakpoints to absolute times.

        Args:
            duration: Total duration of the audio file in seconds

        Returns: List of (time, value) tuples with absolute times
        """
        result = []
        original_order = []  # Track original order for warning

        for point in self.points:
            abs_time = point.get_absolute_time(duration)
            result.append((abs_time, point.value))
            original_order.append((abs_time, point.time))  # Store original time representation

        # Sort by time to ensure ascending order
        result.sort(key=lambda x: x[0])

        # Check if any absolute times are beyond file duration
        for time, original in original_order:
            if isinstance(original, (int, float)) and time > duration:
                import warnings
                warnings.warn(
                    f"Breakpoint at {original}s is beyond file duration {duration:.3f}s. "
                    "This point will be ignored by CDP.",
                    RuntimeWarning
                )

        return result

    def to_file_content(self, duration: float) -> str:
        """
        Generate the content for a CDP breakpoint file.

        Args:
            duration: Total duration of the audio file in seconds

        Returns: String content for the breakpoint file
        """
        absolute_points = self.to_absolute_times(duration)

        lines = []
        for time, value in absolute_points:
            # CDP expects format: "time value" (space-separated, one per line)
            lines.append(f"{time:.6f} {value:.6f}")

        return "\n".join(lines)

    def write_to_file(self, filepath: Path, duration: float) -> Path:
        """
        Write breakpoint data to a file.

        Args:
            filepath: Path to write the file
            duration: Total duration of the audio file in seconds

        Returns: Path to the written file
        """
        content = self.to_file_content(duration)
        Path(filepath).write_text(content)
        return Path(filepath)

    def __len__(self) -> int:
        """Return number of breakpoints."""
        return len(self.points)

    def __str__(self) -> str:
        """String representation."""
        name_str = f"{self.name}: " if self.name else ""
        points_str = ", ".join(f"({p.time}, {p.value})" for p in self.points)
        return f"Breakpoint({name_str}{points_str})"

    @classmethod
    def from_pairs(cls, *pairs: Tuple[Union[float, str], float], name: Optional[str] = None) -> 'Breakpoint':
        """
        Create a Breakpoint from time/value pairs.

        Args:
            pairs: Tuples of (time, value)
            name: Optional name for the breakpoint

        Returns: New Breakpoint instance

        Example:
            bp = Breakpoint.from_pairs(
                (0.0, 5.0),
                ("50%", 10.0),
                ("99%", 2.0)
            )
        """
        bp = cls(name=name)
        for time, value in pairs:
            bp.add(time, value)
        return bp

    @classmethod
    def linear(cls, start_value: float, end_value: float, name: Optional[str] = None) -> 'Breakpoint':
        """
        Create a linear ramp from start to end.

        Args:
            start_value: Value at the beginning
            end_value: Value at the end
            name: Optional name

        Returns: Breakpoint with linear interpolation
        """
        bp = cls(name=name)
        bp.add("0%", start_value)
        bp.add("100%", end_value)
        return bp

    @classmethod
    def fade_in(cls, duration_percent: float = 10.0, max_value: float = 1.0, name: Optional[str] = None) -> 'Breakpoint':
        """
        Create a fade-in curve.

        Args:
            duration_percent: How long the fade takes (as percentage of total)
            max_value: Maximum value after fade
            name: Optional name

        Returns: Breakpoint for fade-in effect
        """
        bp = cls(name=name)
        bp.add("0%", 0.0)
        bp.add(f"{duration_percent}%", max_value)
        bp.add("100%", max_value)
        return bp

    @classmethod
    def fade_out(cls, start_percent: float = 90.0, start_value: float = 1.0, name: Optional[str] = None) -> 'Breakpoint':
        """
        Create a fade-out curve.

        Args:
            start_percent: When the fade starts (as percentage of total)
            start_value: Value before fade starts
            name: Optional name

        Returns: Breakpoint for fade-out effect
        """
        bp = cls(name=name)
        bp.add("0%", start_value)
        bp.add(f"{start_percent}%", start_value)
        bp.add("100%", 0.0)
        return bp


# Type alias for parameters that can be either scalar or automated
AutomatableParam = Union[float, int, Breakpoint]


def is_automatable(value) -> bool:
    """Check if a value is a Breakpoint (automatable parameter)."""
    return isinstance(value, Breakpoint)
