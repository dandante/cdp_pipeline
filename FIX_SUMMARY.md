# Fix Summary: CDP Command Structure with mode_param

## Problem

You tried to run this CDP command:
```bash
specfold specfold 1 inputfile.ana outputfile.ana 1 4 3
```

Using:
```python
specfold_1 = custom_operation("specfold_1", "specfold", "specfold", ["1", "1", "4", "3"])
```

But the library executed:
```bash
specfold specfold first_mono.wav output.ana
```

The issue was that the library didn't understand the CDP command structure where a **numeric mode parameter** comes after the subcommand but before the file arguments.

## Root Cause

Many CDP programs follow this pattern:
```
program subcommand numeric_mode input output params...
```

The library was building commands as:
```
program subcommand input output ALL_PARAMS
```

This meant the numeric mode parameter (which should come before files) was being placed after the files.

## Solution

Added a new `mode_param` field to `CDPOperation` that represents the numeric mode parameter:

### Updated Command Structure

```
program mode mode_param input(s) output params...
```

Example for specfold:
```
specfold specfold 1 input.ana output.ana 1 4 3
         ↑        ↑                       ↑
       mode   mode_param               params
```

### Correct Usage

```python
from cdp_pipeline.operations import custom_operation

specfold_op = custom_operation(
    name="specfold_1",
    program="specfold",
    mode="specfold",
    mode_param=1,       # ← Numeric mode goes here (before files)
    params=[1, 4, 3]    # ← Other params go here (after files)
)
```

This will correctly generate:
```bash
specfold specfold 1 input.ana output.ana 1 4 3
```

## Changes Made

### 1. Updated `cdp_pipeline/core.py`
- Added `mode_param` field to `CDPOperation` class
- Updated `get_command_args()` to insert `mode_param` after mode but before files
- Added documentation explaining command structure

### 2. Updated `cdp_pipeline/operations.py`
- Added `mode_param` parameter to `custom_operation()` function
- Added example in docstring showing correct usage

### 3. Updated Examples
- `examples.py`: Updated example6 to demonstrate `mode_param` with specfold
- `README.md`: Added documentation showing both with and without `mode_param`

### 4. Added Tests
- `test_command_structure.py`: Comprehensive tests for command building
  - Simple commands (blur)
  - Multi-input commands (combine interleave)
  - Commands with mode_param (specfold, pvoc anal)
  - Commands without mode_param

All tests pass ✓

### 5. Added Documentation
- `CHANGELOG.md`: Detailed changelog with migration guide
- `test_specfold.py`: Example script for testing specfold

## Verification

### Command Structure Tests
```bash
python test_command_structure.py
```

Output:
```
Test 1: Simple command (blur) ✓
Test 2: Multi-input command (combine interleave) ✓
Test 3: Command with mode_param (specfold) ✓
Test 4: pvoc anal command ✓
Test 5: Command with only params after files ✓
```

### Basic Library Tests
```bash
python test_basic.py
```

All tests pass ✓

## Examples

### 1. Operation with mode_param (specfold)

```python
from cdp_pipeline import Pipeline
from cdp_pipeline.operations import custom_operation

# Command: specfold specfold 1 input.ana output.ana 1 4 3
specfold_op = custom_operation(
    name="specfold_1",
    program="specfold",
    mode="specfold",
    mode_param=1,
    params=[1, 4, 3]
)

pipeline = Pipeline()
pipeline.add_operation(specfold_op)
pipeline.run("input.wav", "output.wav")
```

### 2. Operation with mode_param (pvoc anal)

```python
# Command: pvoc anal 1 input.wav output.ana
pvoc_anal = custom_operation(
    name="pvoc_anal",
    program="pvoc",
    mode="anal",
    mode_param=1,
    input_format=FileFormat.WAV,
    output_format=FileFormat.ANA
)
```

### 3. Operation without mode_param (blur)

```python
# Command: blur blur input.ana output.ana 2.0
blur_op = custom_operation(
    name="blur_2",
    program="blur",
    mode="blur",
    params=[2.0]  # No mode_param needed
)
```

## Quick Reference

### When to use `mode_param`:

✓ Use when CDP command has numeric mode after subcommand:
```
program subcommand 1 input output params
                   ↑
              mode_param
```

✗ Don't use when all parameters come after files:
```
program subcommand input output param1 param2
                                ↑
                             params
```

### Parameter Placement Rules:

| Parameter | Placement | Example |
|-----------|-----------|---------|
| `program` | First | `specfold` |
| `mode` | After program | `specfold` |
| `mode_param` | After mode, before files | `1` |
| input files | After mode_param | `input.ana` |
| output file | After inputs | `output.ana` |
| `params` | After output | `1 4 3` |

## Testing Your Operation

To test your custom operation, you can:

1. **Print the command structure**:
```python
from cdp_pipeline.core import AudioFile, FileFormat, ChannelMode
from pathlib import Path

op = custom_operation(...)

# Create dummy files
input_file = AudioFile(Path("input.ana"), FileFormat.ANA, ChannelMode.MONO)
output_file = AudioFile(Path("output.ana"), FileFormat.ANA, ChannelMode.MONO)

# Get command args
args = op.get_command_args([input_file], output_file)
print(f"Command: {op.program} {' '.join(args)}")
```

2. **Run with keep_temp=True** to inspect intermediate files:
```python
pipeline.run(
    "input.wav",
    "output.wav",
    keep_temp=True,
    temp_dir="./debug"
)
```

3. **Use test_specfold.py** as a template for your own tests.

## Files Updated

- ✓ `cdp_pipeline/core.py` - Added mode_param field
- ✓ `cdp_pipeline/operations.py` - Updated custom_operation()
- ✓ `examples.py` - Updated example6
- ✓ `README.md` - Added mode_param documentation
- ✓ `test_command_structure.py` - New comprehensive tests
- ✓ `test_specfold.py` - New example test
- ✓ `CHANGELOG.md` - Detailed changelog
- ✓ `FIX_SUMMARY.md` - This file

All tests pass ✓
Library is ready to use!
