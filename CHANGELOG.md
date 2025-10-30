# Changelog

## [0.2.0] - 2025-10-27

### Added
- **Breakpoint automation**: Support for time-varying parameters using CDP breakpoint files
  - New `Breakpoint` class for defining automation curves
  - Support for percentage-based timing (e.g., "50%" = halfway through file)
  - Support for absolute times in seconds
  - Can mix percentages and absolute times
  - Helper methods: `linear()`, `fade_in()`, `fade_out()`, `from_pairs()`
  - Automatic file duration detection using `sndinfo len`
  - Automatic breakpoint file generation and cleanup

  Example:
  ```python
  from cdp_pipeline import Breakpoint

  # Create time-varying parameter
  bp = Breakpoint()
  bp.add("0%", 5.0)
  bp.add("50%", 10.0)
  bp.add("100%", 2.0)

  # Use in operation
  op = custom_operation(
      name="my_effect",
      program="effect",
      params=[bp]  # Pass Breakpoint instead of constant
  )
  ```

- **New files**:
  - `cdp_pipeline/breakpoint.py` - Breakpoint class and utilities
  - `example_breakpoint.py` - Comprehensive examples of breakpoint usage
  - `test_breakpoint.py` - Tests for breakpoint functionality

### Changed
- **PipelineExecutor**: Added `get_duration()` method to get file duration
- **PipelineExecutor**: Added `write_breakpoint_file()` method
- **PipelineExecutor**: Added `_process_breakpoints()` method to handle automation
- **__init__.py**: Exported `Breakpoint`, `BreakpointValue`, `AutomatableParam`, `is_automatable`
- **Documentation**: Added comprehensive breakpoint documentation to README

### Technical Details
- Breakpoints are automatically detected in operation parameters
- File duration is retrieved once per operation
- Breakpoint files are written to temp directory with format: `time value` (space-separated, one per line)
- Percentages are converted to absolute times based on input file duration
- Times are sorted automatically to ensure ascending order

## [0.1.2] - 2025-10-27

### Added
- **Verbose mode**: Added `verbose` parameter to `Pipeline.run()` and `PipelineBuilder.output()` to print CDP commands as they are executed. This is useful for:
  - Debugging pipeline issues
  - Learning how CDP commands work
  - Verifying command structure

  Usage:
  ```python
  pipeline.run("input.wav", "output.wav", verbose=True)
  ```

  Output:
  ```
  Executing: pvoc anal 1 input.wav /tmp/input.ana
  Executing: specfold specfold 1 /tmp/input.ana /tmp/output.ana 1 4 3
  Executing: pvoc synth /tmp/output.ana output.wav
  ```

- **CLI verbose flag**: Added `--verbose` flag to `interleave_v2.py` script:
  ```bash
  python interleave_v2.py --outfile result.wav --verbose file1.wav file2.wav
  ```

### Changed
- **PipelineExecutor**: Added `verbose` parameter to `__init__()`
- **Documentation**: Updated README with verbose mode examples and CLI usage section

## [0.1.1] - 2025-10-27

### Fixed
- **Command structure for CDP operations with numeric modes**: Many CDP programs have a command structure like:
  ```
  program subcommand numeric_mode input output params...
  ```
  For example: `specfold specfold 1 input.ana output.ana 1 4 3`

  The library was not handling the numeric mode parameter correctly, placing all parameters after the files.

### Added
- **`mode_param` field to `CDPOperation`**: New optional field for numeric mode parameters that come after the mode/subcommand but before the file arguments.

- **Updated `custom_operation()` function**: Now accepts `mode_param` parameter:
  ```python
  custom_operation(
      name="specfold_1",
      program="specfold",
      mode="specfold",
      mode_param=1,      # Goes here: after mode, before files
      params=[1, 4, 3]   # Goes here: after files
  )
  ```

- **Command structure tests**: Added comprehensive tests in `test_command_structure.py` to verify correct command building for:
  - Simple commands (blur)
  - Multi-input commands (combine interleave)
  - Commands with mode_param (specfold, pvoc anal)
  - Commands with only params after files

### Changed
- **Updated documentation**:
  - README.md now shows correct usage of `mode_param` in custom operations
  - examples.py updated with correct specfold example
  - Added inline comments explaining command structure

### Command Structure Reference

CDP commands follow this general pattern:

```
program [mode] [mode_param] input(s) output [params...]
```

Examples:

1. **Simple operation** (no mode_param):
   ```
   blur blur input.ana output.ana 2.0
   ```

2. **Multi-input operation**:
   ```
   combine interleave input1.ana input2.ana input3.ana output.ana 1
   ```

3. **Operation with mode_param**:
   ```
   specfold specfold 1 input.ana output.ana 1 4 3
                    ↑                        ↑
                mode_param                 params
   ```

4. **Conversion operation**:
   ```
   pvoc anal 1 input.wav output.ana
            ↑
        mode_param
   ```

### How to Use

```python
from cdp_pipeline.operations import custom_operation

# For operations WITH numeric mode parameter:
op = custom_operation(
    name="operation_name",
    program="cdp_program",
    mode="subcommand",
    mode_param=1,        # ← Add this for numeric mode
    params=[other, params]
)

# For operations WITHOUT numeric mode parameter:
op = custom_operation(
    name="operation_name",
    program="cdp_program",
    mode="subcommand",
    params=[all, params]  # All params go after files
)
```

### Testing

Run the command structure tests to verify:

```bash
python test_command_structure.py
```

All tests should pass, confirming that commands are built correctly.

### Migration Guide

If you have existing custom operations that were trying to work around this issue, update them:

**Before (incorrect)**:
```python
# This would produce: specfold specfold input.ana output.ana 1 1 4 3
custom_operation("specfold", "specfold", "specfold", params=[1, 1, 4, 3])
```

**After (correct)**:
```python
# This produces: specfold specfold 1 input.ana output.ana 1 4 3
custom_operation(
    name="specfold_1",
    program="specfold",
    mode="specfold",
    mode_param=1,      # Numeric mode goes here
    params=[1, 4, 3]   # Other params go here
)
```

## [0.1.0] - 2025-10-27

### Added
- Initial release of CDP Pipeline library
- Automatic format conversion (WAV ↔ ANA)
- Automatic channel handling (stereo ↔ mono)
- Pipeline composition API
- Pre-defined operations (blur, interleave, morph, etc.)
- PipelineBuilder fluent API
- Comprehensive documentation and examples
