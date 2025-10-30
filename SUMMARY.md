# CDP Pipeline Library - Summary

## What We Built

A general-purpose Python library for composing CDP audio processing workflows with automatic format conversion and channel handling.

## Project Structure

```
cdp_pipeline/
├── __init__.py       - Package exports and main API
├── core.py          - Core data structures (AudioFile, CDPOperation, etc.)
├── operations.py    - Pre-defined CDP operations (blur, interleave, morph, etc.)
├── executor.py      - Execution engine with format/channel conversion
└── pipeline.py      - Pipeline composition (Pipeline, PipelineBuilder)

Supporting files:
├── interleave_v2.py - Rewritten version of your original script (30 lines vs 160!)
├── examples.py      - 10 comprehensive usage examples
├── test_basic.py    - Basic test suite (all passing ✓)
├── setup.py         - Package installation script
├── README.md        - Complete documentation
└── SUMMARY.md       - This file
```

## Key Features

### 1. Automatic Format Conversion
- Transparently converts between WAV and spectral analysis (.ana) formats
- Uses `pvoc anal` (WAV → ANA) and `pvoc synth` (ANA → WAV) automatically
- Handles mixed spectral and time-domain operations in same pipeline

### 2. Automatic Channel Handling
- Splits stereo files into mono channels using `housekeep chans`
- Processes each channel independently through the pipeline
- Merges channels back to stereo using `submix interleave`
- Works seamlessly with multi-input operations

### 3. Pipeline Composition
- Chain multiple CDP operations together
- Two APIs: explicit `Pipeline` class or fluent `PipelineBuilder`
- Automatic temporary file management with cleanup

### 4. Extensible Design
- Easy to add new CDP operations via `custom_operation()`
- Pre-defined operations for common tasks
- Type-safe with clear data structures

## Comparison: Before vs After

### Original interleave.py (160 lines)
```python
# Manual everything:
# - Check channels with sfprops
# - Copy files to temp directory
# - Split stereo with housekeep chans
# - Convert to ANA with pvoc anal
# - Group files by channel
# - Run combine interleave per channel
# - Convert back with pvoc synth
# - Merge stereo with submix
# - Clean up temp files
```

### New interleave_v2.py (30 lines)
```python
pipeline = Pipeline()
pipeline.add_operation(combine_interleave(leafsize=leafsize))
pipeline.run(input_files, output_file)
# Done! Library handles all the complexity.
```

## Test Results

✓ All imports successful
✓ AudioFile class works correctly
✓ Operations created correctly
✓ Pipeline composition works
✓ PipelineBuilder works
✓ PipelineExecutor initialization works
✓ Real file processing: Successfully processed zorb4.wav + zorb10.wav → test_output.wav (22M)

## Architecture Highlights

### Core Abstractions

**AudioFile**: Represents a file with metadata
- Path, format (WAV/ANA), channels (MONO/STEREO)
- Channel index for split stereo files
- Methods: `with_extension()`, `with_suffix()`

**CDPOperation**: Represents a CDP command
- Program name, mode, parameters
- Input requirements (format + channels)
- Output format
- Multi-input flag for operations like combine

**Pipeline**: Chains operations
- Add operations with `add_operation()`
- Execute with `run()`
- Handles all format/channel conversions automatically

**PipelineExecutor**: Low-level execution engine
- Format conversion: `convert_to_ana()`, `convert_to_wav()`
- Channel manipulation: `split_stereo()`, `merge_stereo()`
- Operation execution: `execute_operation()`
- Temp file management

## Usage Examples

### Simple blur
```python
from cdp_pipeline import Pipeline
from cdp_pipeline.operations import blur

pipeline = Pipeline()
pipeline.add_operation(blur(2.0))
pipeline.run("input.wav", "output.wav")
```

### Chained operations
```python
pipeline = Pipeline()
pipeline.add_operation(blur(1.5))
pipeline.add_operation(pitch_transpose(5.0))
pipeline.add_operation(stretch(1.5))
pipeline.run("input.wav", "processed.wav")
```

### Fluent API
```python
from cdp_pipeline import PipelineBuilder

result = (PipelineBuilder(["file1.wav", "file2.wav"])
          .add(combine_interleave(1))
          .add(blur(2.0))
          .output("result.wav"))
```

### Custom operation
```python
from cdp_pipeline.operations import custom_operation
from cdp_pipeline.core import FileFormat, ChannelMode

my_op = custom_operation(
    name="my_effect",
    program="cdp_program",
    mode="mode_name",
    input_format=FileFormat.ANA,
    output_format=FileFormat.ANA,
    channels=ChannelMode.MONO,
    params=[1.0, 2.0]
)

pipeline = Pipeline()
pipeline.add_operation(my_op)
pipeline.run("input.wav", "output.wav")
```

## How It Works

### Automatic Format Flow

When you run a pipeline, the executor:

1. **Loads inputs**: Creates `AudioFile` objects with metadata
2. **For each operation**:
   - Checks operation's input requirements
   - Converts format if needed (WAV ↔ ANA)
   - Handles channel splitting if needed (STEREO → MONO channels)
   - Executes the CDP command
   - Tracks output files with correct metadata
3. **Finalizes output**:
   - Converts to desired output format
   - Merges channels if needed (MONO channels → STEREO)
   - Copies to output path
   - Cleans up temp files

### Per-Channel Processing

For stereo files + mono-only operations:
1. Split: `stereo.wav` → `file_c1.wav`, `file_c2.wav`
2. Process left: `file_c1.wav` → ... → `out_c1.wav`
3. Process right: `file_c2.wav` → ... → `out_c2.wav`
4. Merge: `out_c1.wav` + `out_c2.wav` → `output.wav` (stereo)

### Multi-Input Operations

For operations like `combine interleave` with multiple stereo inputs:
1. Split all inputs to channels
2. Group by channel: [file1_c1, file2_c1, file3_c1], [file1_c2, file2_c2, file3_c2]
3. Process each group: combine([...c1...]) → out_c1, combine([...c2...]) → out_c2
4. Merge: out_c1 + out_c2 → output (stereo)

## Next Steps / Future Enhancements

### Immediate Opportunities

1. **Add more operations** - The library currently has ~10 predefined operations, but CDP has hundreds. Easy to add more in `operations.py`.

2. **CLI tool** - Create a general CLI like `cdp-pipeline run pipeline.yaml` for running pipelines from config files.

3. **YAML pipeline definitions**:
   ```yaml
   pipeline:
     - blur: 2.0
     - pitch_transpose: 5.0
     - stretch: 1.5
   input: input.wav
   output: output.wav
   ```

4. **Better error handling** - More descriptive error messages when CDP commands fail.

5. **Parameter validation** - Validate operation parameters against CDP's requirements.

### Advanced Features

1. **Parallel channel processing** - Process left/right channels in parallel for speed.

2. **Caching** - Cache intermediate results to avoid recomputation when experimenting.

3. **Dry-run mode** - Show what commands will be executed without running them.

4. **Progress callbacks** - Report progress for long-running operations:
   ```python
   def progress_callback(step, total, operation):
       print(f"[{step}/{total}] {operation}")

   pipeline.run(..., progress_callback=progress_callback)
   ```

5. **Operation composition** - Create reusable operation groups:
   ```python
   spectral_shimmer = OperationGroup([
       blur(1.5),
       pitch_transpose(0.1),
       stretch(1.01)
   ])

   pipeline.add_operation(spectral_shimmer)
   ```

6. **Conditional operations** - Apply operations based on file properties:
   ```python
   pipeline.add_operation(
       blur(2.0),
       condition=lambda f: f.duration > 5.0
   )
   ```

7. **Batch processing** - Process multiple files through same pipeline:
   ```python
   pipeline.run_batch(
       input_files=["file1.wav", "file2.wav", "file3.wav"],
       output_pattern="processed_{input}.wav"
   )
   ```

### Documentation

1. **Video tutorials** - Screen recordings showing common workflows.

2. **CDP operation catalog** - Document all CDP operations with examples.

3. **Cookbook** - Common recipes for specific sound design tasks.

4. **API reference** - Auto-generated docs from docstrings.

## Known Issues / Considerations

1. **CDP binary compatibility** - Some systems may have issues with CDP binaries (as seen with the `sfprops` error). The library uses the `sh` module which assumes binaries are in PATH and executable.

2. **Error messages** - When CDP commands fail, error messages could be more helpful.

3. **Format detection** - For `.ana` files, channel count isn't automatically detectable. Currently assumes mono unless specified.

4. **Large files** - No streaming support yet. All operations load entire files.

5. **Thread safety** - Not designed for concurrent use of same PipelineExecutor instance.

## Installation & Usage

### Setup
```bash
# Install in development mode
pip install -e .

# Or just use directly (no installation needed)
python interleave_v2.py --help
```

### Run Examples
```bash
# Test basic functionality
python test_basic.py

# Run the rewritten interleave script
python interleave_v2.py --outfile result.wav --leafsize 1 file1.wav file2.wav

# See more examples
python examples.py
```

### As a Library
```python
from cdp_pipeline import Pipeline
from cdp_pipeline.operations import blur, pitch_transpose

pipeline = Pipeline()
pipeline.add_operation(blur(2.0))
pipeline.add_operation(pitch_transpose(3.5))
pipeline.run("input.wav", "output.wav")
```

## Conclusion

The CDP Pipeline library successfully abstracts away the complexity of working with CDP tools. What previously required 160 lines of careful manual file management now takes just a few lines of clear, declarative code.

The architecture is extensible and well-structured, making it easy to:
- Add new CDP operations
- Compose complex processing chains
- Handle stereo/mono conversions transparently
- Manage temporary files automatically

The library is ready for use and can serve as a foundation for more advanced CDP workflows, CLI tools, and audio processing applications.
