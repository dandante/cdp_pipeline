# CDP Pipeline

A Python library for composing audio processing workflows using the Composers' Desktop Project (CDP) tools.

## Overview

The CDP contains hundreds of powerful audio processing tools, but they can be complex to use:
- Different tools work on different file formats (WAV vs spectral analysis)
- Stereo files need to be split, processed per-channel, then re-merged
- Format conversions between WAV and analysis files must be managed manually
- Temporary files must be tracked and cleaned up

**CDP Pipeline** solves these problems by providing a high-level API that handles all the complexity automatically.

## Features

- **Automatic Format Conversion**: Seamlessly converts between WAV and spectral analysis formats
- **Transparent Channel Handling**: Automatically splits stereo files, processes per-channel, and re-merges
- **Pipeline Composition**: Chain multiple operations together
- **Temporary File Management**: Automatic cleanup of intermediate files
- **Type Safety**: Clear data structures for files, formats, and operations
- **Extensible**: Easy to add custom CDP operations

## Installation

```bash
# Ensure CDP tools are installed and in your PATH
# Then install dependencies:
pip install -r requirements.txt
```

The library requires:
- Python 3.7+
- CDP tools installed and accessible
- `sh` library for command execution
- `click` (optional, for CLI scripts)

## Quick Start

### Simple Example

```python
from cdp_pipeline import Pipeline
from cdp_pipeline.operations import blur

# Create a pipeline
pipeline = Pipeline()
pipeline.add_operation(blur(2.0))

# Run it - the library handles all conversions automatically
pipeline.run("input.wav", "output.wav")
```

### Chaining Operations

```python
from cdp_pipeline import Pipeline
from cdp_pipeline.operations import blur, pitch_transpose, stretch

pipeline = Pipeline()
pipeline.add_operation(blur(1.5))
pipeline.add_operation(pitch_transpose(5.0))
pipeline.add_operation(stretch(1.5))

pipeline.run("input.wav", "processed.wav")
```

### Multiple Input Files

```python
from cdp_pipeline import Pipeline
from cdp_pipeline.operations import combine_interleave

pipeline = Pipeline()
pipeline.add_operation(combine_interleave(leafsize=1))

# Works with both mono and stereo files
pipeline.run(
    ["file1.wav", "file2.wav", "file3.wav"],
    "interleaved.wav"
)
```

### Fluent API with PipelineBuilder

```python
from cdp_pipeline import PipelineBuilder
from cdp_pipeline.operations import combine_interleave, blur, pitch_transpose

result = (PipelineBuilder(["input1.wav", "input2.wav"])
          .add(combine_interleave(leafsize=2))
          .add(blur(1.5))
          .add(pitch_transpose(-3.0))
          .output("result.wav"))
```

## How It Works

### Automatic Format Conversion

CDP has two main file types:
- **WAV files**: Standard audio format
- **ANA files**: Spectral analysis format (from pvoc analysis)

Some operations work on WAV files (time-domain processing), others on ANA files (spectral processing).

The library automatically:
1. Detects what format each operation needs
2. Converts files to the required format using `pvoc anal` (WAV → ANA) or `pvoc synth` (ANA → WAV)
3. Chains conversions efficiently

```python
# This pipeline mixes spectral and time-domain operations
pipeline = Pipeline()
pipeline.add_operation(blur(2.0))          # Spectral (needs ANA)
pipeline.add_operation(modify_speed(0.5))  # Time-domain (needs WAV)
pipeline.add_operation(stretch(2.0))       # Spectral (needs ANA)

# The library handles all conversions:
# input.wav → convert to ANA → blur → convert to WAV → modify_speed
# → convert to ANA → stretch → convert to WAV → output.wav
pipeline.run("input.wav", "output.wav")
```

### Automatic Channel Handling

For stereo files, the library:
1. Splits stereo into left and right channels using `housekeep chans`
2. Processes each channel separately through the pipeline
3. Merges channels back to stereo using `submix interleave`

```python
pipeline = Pipeline()
pipeline.add_operation(blur(2.0))

# Input is stereo (2 channels)
# Library automatically:
# 1. Splits to left.wav and right.wav
# 2. Converts each to ANA: left.ana, right.ana
# 3. Processes: blur(left.ana) → left_out.ana
#              blur(right.ana) → right_out.ana
# 4. Converts back: left_out.wav, right_out.wav
# 5. Merges to stereo: output.wav
pipeline.run("stereo_input.wav", "stereo_output.wav")
```

### Multi-Input Operations

Some operations (like `combine interleave`) take multiple input files:

```python
# The library handles per-channel processing automatically:
# If inputs are stereo, it:
# 1. Splits all inputs to mono channels
# 2. Groups by channel (all left channels together, all right together)
# 3. Runs operation on each channel group
# 4. Merges back to stereo

pipeline = Pipeline()
pipeline.add_operation(combine_interleave(leafsize=1))

pipeline.run(
    ["stereo1.wav", "stereo2.wav", "stereo3.wav"],
    "interleaved_stereo.wav"
)
```

## API Reference

### Core Classes

#### `AudioFile`

Represents an audio or analysis file with metadata.

```python
from cdp_pipeline.core import AudioFile, FileFormat, ChannelMode

audio = AudioFile(
    path="file.wav",
    format=FileFormat.WAV,
    channels=ChannelMode.STEREO
)
```

#### `CDPOperation`

Represents a CDP command with its requirements.

```python
from cdp_pipeline.core import CDPOperation, OperationRequirements, FileFormat, ChannelMode

operation = CDPOperation(
    name="blur_2.0",
    program="blur",
    subcommand="blur",
    input_requirements=OperationRequirements(FileFormat.ANA, ChannelMode.MONO),
    output_format=FileFormat.ANA,
    params=[2.0]
)
```

#### `Pipeline`

Chains operations together.

```python
from cdp_pipeline import Pipeline

pipeline = Pipeline()
pipeline.add_operation(operation1)
pipeline.add_operation(operation2)

result = pipeline.run(
    input_files="input.wav",
    output_file="output.wav",
    temp_dir=None,           # Auto-create temp dir
    keep_temp=False,         # Delete temp files after
    output_channels=None,    # Preserve input channel config
    output_format=None       # Default to WAV
)
```

#### `PipelineExecutor`

Low-level execution engine (usually used internally).

```python
from cdp_pipeline import PipelineExecutor

with PipelineExecutor(temp_dir="./temp", keep_temp=True) as executor:
    # Split stereo
    channels = executor.split_stereo(audio_file)

    # Convert formats
    ana_file = executor.convert_to_ana(wav_file)
    wav_file = executor.convert_to_wav(ana_file)

    # Execute operation
    outputs = executor.execute_operation(operation, inputs)
```

### Pre-defined Operations

All operations are in `cdp_pipeline.operations`:

#### Spectral Processing (work on .ana files)

```python
from cdp_pipeline.operations import (
    blur,              # Spectral blurring
    combine_interleave,# Interleave multiple files
    morph,             # Morph between sounds
    pitch_transpose,   # Pitch shifting
    stretch,           # Time stretching
)

# Usage:
blur(blur_amount=2.0)
combine_interleave(leafsize=1)
morph(morphing_factor=0.5)
pitch_transpose(semitones=5.0)
stretch(time_stretch=1.5)
```

#### Time Domain (work on .wav files)

```python
from cdp_pipeline.operations import (
    modify_speed,    # Change speed
    envel_attack,    # Envelope shaping
    filter_lohi,     # Low-pass or high-pass filter
)

# Usage:
modify_speed(speed=2.0)
envel_attack(attack_time=0.5)

# Low-pass filter (stop_band > pass_band)
filter_lohi(attenuation=-60, pass_band=1000, stop_band=2000, mode=1)

# High-pass filter (stop_band < pass_band)
filter_lohi(attenuation=-60, pass_band=2000, stop_band=1000, mode=1)
```

#### Custom Operations

```python
from cdp_pipeline.operations import custom_operation
from cdp_pipeline.core import FileFormat, ChannelMode

# Define your own CDP operation
# Example: specfold specfold 1 input.ana output.ana 1 4 3
my_op = custom_operation(
    name="specfold_1",
    program="specfold",
    subcommand="specfold",
    mode=1,                 # Numeric mode (comes after subcommand, before files)
    input_format=FileFormat.ANA,
    output_format=FileFormat.ANA,
    channels=ChannelMode.MONO,
    params=[1, 4, 3],       # Additional params (come after files)
    multi_input=False
)

# For operations without a numeric mode, omit mode:
simple_op = custom_operation(
    name="blur_custom",
    program="blur",
    subcommand="blur",
    params=[2.0]  # Only params after files
)
```

### Breakpoint Automation - Time-Varying Parameters

CDP supports **breakpoint files** for parameters that vary over time. The library makes this easy with the `Breakpoint` class.

#### Basic Usage

```python
from cdp_pipeline import Breakpoint

# Create a time-varying parameter using percentages
bp = Breakpoint()
bp.add("0%", 5.0)    # At start: value is 5.0
bp.add("50%", 10.0)  # At midpoint: value is 10.0
bp.add("99%", 2.0)   # Near end: value is 2.0

# Use it in an operation
my_op = custom_operation(
    name="my_effect",
    program="effect",
    params=[bp]  # Pass Breakpoint instead of a constant value
)
```

#### Why Use Percentages?

Percentages are relative to the input file duration, so you don't need to know the exact file length:

```python
# For a 2-second file:
#   0% (0.0s) -> 5.0
#   50% (1.0s) -> 10.0
#   99% (1.98s) -> 2.0

# For a 10-second file:
#   0% (0.0s) -> 5.0
#   50% (5.0s) -> 10.0
#   99% (9.9s) -> 2.0
```

#### Helper Methods

```python
# Linear ramp
fade_up = Breakpoint.linear(0.0, 1.0)

# Fade in over first 10%
fade_in = Breakpoint.fade_in(duration_percent=10.0, max_value=1.0)

# Fade out starting at 90%
fade_out = Breakpoint.fade_out(start_percent=90.0, start_value=1.0)

# Create from pairs
custom = Breakpoint.from_pairs(
    ("0%", 1.0),
    ("25%", 0.5),
    ("75%", 0.5),
    ("100%", 1.0)
)
```

#### Mixing Absolute Times and Percentages

You *can* mix absolute times and percentages, but be careful:

```python
bp = Breakpoint()
bp.add(0.0, 0.0)      # Absolute: at 0.0 seconds
bp.add(0.5, 1.0)      # Absolute: at 0.5 seconds
bp.add("50%", 0.5)    # Relative: at 50% of duration
bp.add("100%", 0.0)   # Relative: at the end

# For a 4-second file: 0.0s, 0.5s, 2.0s, 4.0s ✓
# For a 0.3-second file: 0.0s, 0.15s, 0.3s, 0.5s ✗ (0.5s is beyond file end!)
```

**Best practice**: Use all percentages OR all absolute times, not a mix, unless you're certain about the file duration.

#### When to Use Breakpoints vs Constants

```python
# Constant parameter (same value throughout)
constant_blur = 2.0

# Time-varying parameter (changes over time)
varying_blur = Breakpoint.from_pairs(
    ("0%", 1.0),
    ("50%", 5.0),
    ("100%", 1.0)
)

# Use in operation
blur_op = custom_operation(
    name="blur_sweep",
    program="blur",
    params=[varying_blur]  # or [constant_blur] for constant
)
```

#### How It Works

When you use a `Breakpoint` in a pipeline:

1. The library gets the input file duration using `sndinfo len`
2. Converts percentage times to absolute seconds
3. Writes a CDP breakpoint file with format: `time value` (one per line)
4. Passes the breakpoint file path to the CDP command

With `verbose=True`, you'll see:
```
Executing: sndinfo len input.wav
Created breakpoint file: /tmp/operation_param0_0001.txt
  Content:
  0.000000 5.000000
  1.000000 10.000000
  1.980000 2.000000
Executing: effect input.wav output.wav /tmp/operation_param0_0001.txt
```

#### Example: Filter Sweep

```python
from cdp_pipeline import Pipeline, Breakpoint
from cdp_pipeline.operations import custom_operation

# Create a sweeping cutoff frequency
cutoff_sweep = Breakpoint.from_pairs(
    ("0%", 200.0),    # Start at 200 Hz
    ("30%", 2000.0),  # Sweep up
    ("70%", 2000.0),  # Hold
    ("100%", 200.0)   # Sweep back down
)

filter_op = custom_operation(
    name="filter_sweep",
    program="filter",
    subcommand="lopass",
    params=[cutoff_sweep]
)

pipeline = Pipeline()
pipeline.add_operation(filter_op)
pipeline.run("input.wav", "output.wav", verbose=True)
```

See `example_breakpoint.py` for more examples.

## Advanced Usage

### Verbose Mode - See Commands Being Executed

Enable verbose mode to see the actual CDP commands being executed:

```python
pipeline.run(
    "input.wav",
    "output.wav",
    verbose=True
)
```

Output:
```
Executing: pvoc anal 1 input.wav /tmp/tmp123/input_0001.ana
Executing: specfold specfold 1 /tmp/tmp123/input_0001.ana /tmp/tmp123/op00_specfold_1_0002.ana 1 4 3
Executing: pvoc synth /tmp/tmp123/op00_specfold_1_0002.ana /tmp/tmp123/op00_specfold_1_0003.wav
```

This is very useful for:
- Debugging pipeline issues
- Learning how CDP commands work
- Verifying the correct command structure

### Keeping Temporary Files for Debugging

```python
pipeline.run(
    "input.wav",
    "output.wav",
    temp_dir="./debug",
    keep_temp=True,
    verbose=True  # Combine with verbose to see what's happening
)
# Temp files remain in ./debug/ for inspection
```

### Controlling Output Format

```python
from cdp_pipeline.core import FileFormat

# Output as spectral analysis file
pipeline.run(
    "input.wav",
    "output.ana",
    output_format=FileFormat.ANA
)
```

### Mixed Channel Outputs

```python
from cdp_pipeline.core import ChannelMode

# Force mono output even if input is stereo
pipeline.run(
    "stereo.wav",
    "mono.wav",
    output_channels=ChannelMode.MONO
)
```

### Using the MCP Server

The CDP MCP server provides additional tools for working with CDP:

```python
# List available CDP programs
mcp__cdp__list_cdp_programs()

# Get usage info
mcp__cdp__get_cdp_usage("blur")

# Execute CDP command directly
mcp__cdp__execute_cdp(["blur", "blur", "input.ana", "output.ana", "2.0"])

# Analyze sound file
mcp__cdp__analyze_sound("file.wav")
```

## Project Structure

```
cdp_pipeline/
├── __init__.py       # Package exports
├── core.py           # Core data structures (AudioFile, CDPOperation)
├── operations.py     # Pre-defined CDP operations
├── executor.py       # Execution engine (format conversion, channel handling)
└── pipeline.py       # Pipeline composition (Pipeline, PipelineBuilder)

examples.py           # Usage examples
interleave_v2.py      # Rewritten version of original script
README.md             # This file
```

## Comparison: Before and After

### Before (Manual Approach)

```python
# Original interleave.py - 160 lines
# Manually:
# - Check channels
# - Copy to temp
# - Split stereo
# - Convert to ANA
# - Process per channel
# - Convert back to WAV
# - Merge stereo
# - Clean up temp files
```

### After (Using CDP Pipeline)

```python
# interleave_v2.py - 30 lines
from cdp_pipeline import Pipeline
from cdp_pipeline.operations import combine_interleave

pipeline = Pipeline()
pipeline.add_operation(combine_interleave(leafsize=1))
pipeline.run(input_files, output_file)
```

## Extending the Library

### Adding New Operations

1. Add a function in `operations.py`:

```python
def my_new_operation(param1: float, param2: int) -> CDPOperation:
    """
    Description of what this operation does.

    Args:
        param1: Description
        param2: Description
    """
    return CDPOperation(
        name=f"my_op_{param1}",
        program="cdp_program",
        subcommand="subcommand",
        input_requirements=OperationRequirements(FileFormat.ANA, ChannelMode.MONO),
        output_format=FileFormat.ANA,
        params=[param1, param2]
    )
```

2. Use it in pipelines:

```python
from cdp_pipeline.operations import my_new_operation

pipeline.add_operation(my_new_operation(1.5, 3))
```

### Contributing CDP Operation Definitions

The library includes common operations, but CDP has hundreds of programs. Contributions of well-documented operation definitions are welcome!

## CLI Usage

The `interleave_v2.py` script demonstrates CLI usage:

```bash
# Basic usage
python interleave_v2.py --outfile result.wav file1.wav file2.wav

# With options
python interleave_v2.py --outfile result.wav --leafsize 2 file1.wav file2.wav

# Show commands being executed
python interleave_v2.py --outfile result.wav --verbose file1.wav file2.wav

# Keep temporary files for debugging
python interleave_v2.py --outfile result.wav --keep-temp --verbose file1.wav file2.wav
```

Available flags:
- `--leafsize N`: Leaf size parameter for interleaving (default: 1)
- `--outfile FILE`: Output file path (required)
- `--verbose`: Print CDP commands as they are executed
- `--keep-temp`: Keep temporary files after execution

## Future Enhancements

Potential areas for expansion:

- **Enhanced CLI Tool**: More general command-line interface for running any pipeline
- **YAML Pipeline Definitions**: Define pipelines in configuration files
- **Parallel Processing**: Process channels in parallel for speed
- **Caching**: Cache intermediate results to avoid recomputation
- **More Operations**: Add more pre-defined CDP operations
- **Validation**: Validate operation parameters against CDP requirements
- **Progress Callbacks**: Report progress for long-running operations
- **Dry-run Mode**: Preview what commands will be executed

## License

[GPL v3](https://www.gnu.org/licenses/gpl-3.0.en.html)

## Credits

Built for working with the Composers' Desktop Project (CDP).
CDP: https://www.composersdesktop.com/
