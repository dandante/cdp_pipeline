"""
CDP Pipeline - A Python library for composing CDP audio processing workflows.

This library provides a high-level API for chaining CDP (Composers Desktop Project)
operations with automatic format conversion and channel handling.

Basic usage:
    from cdp_pipeline import Pipeline
    from cdp_pipeline.operations import blur, pitch_transpose

    pipeline = Pipeline()
    pipeline.add_operation(blur(2.0))
    pipeline.add_operation(pitch_transpose(3.5))
    pipeline.run(["input1.wav", "input2.wav"], "output.wav")

Using PipelineBuilder:
    from cdp_pipeline import PipelineBuilder
    from cdp_pipeline.operations import combine_interleave

    result = (PipelineBuilder(["file1.wav", "file2.wav"])
              .add(combine_interleave(leafsize=1))
              .output("result.wav"))
"""

__version__ = "0.1.0"

from .core import (
    AudioFile,
    FileFormat,
    ChannelMode,
    CDPOperation,
    OperationRequirements
)

from .pipeline import (
    Pipeline,
    PipelineBuilder
)

from .executor import PipelineExecutor

from .breakpoint import (
    Breakpoint,
    BreakpointValue,
    AutomatableParam,
    is_automatable
)

# Import common operations for convenience
from . import operations

__all__ = [
    # Core classes
    "AudioFile",
    "FileFormat",
    "ChannelMode",
    "CDPOperation",
    "OperationRequirements",

    # Pipeline
    "Pipeline",
    "PipelineBuilder",
    "PipelineExecutor",

    # Breakpoint automation
    "Breakpoint",
    "BreakpointValue",
    "AutomatableParam",
    "is_automatable",

    # Operations module
    "operations",
]
