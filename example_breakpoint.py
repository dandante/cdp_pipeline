#!/usr/bin/env python3

"""
Example demonstrating breakpoint automation for time-varying parameters.
"""

from cdp_pipeline import Pipeline, Breakpoint
from cdp_pipeline.operations import custom_operation
from cdp_pipeline.core import FileFormat, ChannelMode


def example_simple_breakpoint():
    """
    Example: Using a breakpoint for time-varying parameter.

    This demonstrates the basic usage of breakpoints with percentages.
    """
    print("Example 1: Simple breakpoint with percentages")
    print("-" * 60)

    # Create a breakpoint that varies over time
    # Start at 5.0, ramp up to 10.0 at the halfway point, then down to 2.0 near the end
    bp = Breakpoint()
    bp.add("0%", 5.0)
    bp.add("50%", 10.0)
    bp.add("99%", 2.0)

    print(f"Breakpoint: {bp}")
    print("\nThis will be converted to absolute times based on the input file duration.")
    print("For a 2-second file:")
    print("  0% (0.0s) -> 5.0")
    print("  50% (1.0s) -> 10.0")
    print("  99% (1.98s) -> 2.0")
    print()


def example_helper_methods():
    """
    Example: Using helper methods to create common breakpoint patterns.
    """
    print("\nExample 2: Breakpoint helper methods")
    print("-" * 60)

    # Linear ramp from 0 to 1
    fade_up = Breakpoint.linear(0.0, 1.0, name="fade_up")
    print(f"Linear fade up: {fade_up}")

    # Fade in over first 10% of duration
    fade_in = Breakpoint.fade_in(duration_percent=10.0, max_value=1.0)
    print(f"Fade in: {fade_in}")

    # Fade out starting at 90% of duration
    fade_out = Breakpoint.fade_out(start_percent=90.0, start_value=1.0)
    print(f"Fade out: {fade_out}")

    # Create from pairs - using only percentages for clarity
    custom = Breakpoint.from_pairs(
        ("0%", 1.0),
        ("25%", 0.5),
        ("75%", 0.5),
        ("100%", 1.0),
        name="custom_shape"
    )
    print(f"Custom shape: {custom}")
    print("\n  Note: It's best to use either all percentages or all absolute times")
    print("  to avoid confusion about chronological ordering.")
    print()


def example_with_operation():
    """
    Example: Using breakpoint in an actual operation.

    Note: This creates the pipeline but doesn't run it (requires an input file).
    """
    print("\nExample 3: Using breakpoint with CDP operation")
    print("-" * 60)

    # Create a time-varying parameter for an effect
    # Let's say we want to vary the blur amount over time
    blur_automation = Breakpoint()
    blur_automation.add("0%", 1.0)    # Start with mild blur
    blur_automation.add("50%", 5.0)   # Peak blur in the middle
    blur_automation.add("100%", 1.0)  # Return to mild blur

    # Note: blur typically takes a constant parameter, but this shows the concept
    # For a real example, you'd use an operation that explicitly supports
    # time-varying parameters (indicated in CDP docs)

    print(f"Blur automation: {blur_automation}")
    print("\nWhen this pipeline runs:")
    print("1. The library gets the input file duration")
    print("2. Converts percentage times to absolute seconds")
    print("3. Writes a breakpoint file with the absolute times")
    print("4. Passes the breakpoint filename to the CDP command")
    print()


def example_constant_vs_varying():
    """
    Example: When to use constant values vs breakpoints.
    """
    print("\nExample 4: Constant vs time-varying parameters")
    print("-" * 60)

    print("Use a constant value (simple number) when:")
    print("  - The parameter should stay the same throughout")
    print("  - Example: blur amount of 2.0")
    print()

    print("Use a breakpoint when:")
    print("  - The parameter should change over time")
    print("  - Example: gradual fade in/out")
    print("  - Example: sweeping filter cutoff")
    print("  - Example: varying distortion intensity")
    print()

    # Constant parameter
    constant_param = 2.0
    print(f"Constant parameter: {constant_param}")

    # Time-varying parameter
    varying_param = Breakpoint.fade_in(10.0, 1.0)
    print(f"Time-varying parameter: {varying_param}")
    print()


def example_absolute_times():
    """
    Example: Using absolute times instead of percentages.
    """
    print("\nExample 5: Using absolute times")
    print("-" * 60)

    # You can mix absolute times and percentages, but be careful!
    bp = Breakpoint()
    bp.add(0.0, 0.0)      # Start at 0.0 seconds
    bp.add(0.5, 1.0)      # At 0.5 seconds
    bp.add("50%", 0.5)    # At 50% of duration
    bp.add("100%", 0.0)   # At the end

    print(f"Mixed times: {bp}")
    print("\nFor a 4-second file, this becomes:")
    print("  0.0s -> 0.0")
    print("  0.5s -> 1.0")
    print("  2.0s (50%) -> 0.5")
    print("  4.0s (100%) -> 0.0")

    print("\nWarning: For a 0.3-second file, this would become:")
    print("  0.0s -> 0.0")
    print("  0.15s (50%) -> 0.5")
    print("  0.3s (100%) -> 0.0")
    print("  0.5s -> 1.0  ← This is AFTER the end of the file!")
    print("\nBest practice: Use all percentages OR all absolute times,")
    print("not a mix, unless you're certain about the file duration.")
    print()


def example_real_world_usage():
    """
    Example: Real-world usage pattern.
    """
    print("\nExample 6: Real-world usage pattern")
    print("-" * 60)

    # Suppose you want to apply a filter with a time-varying cutoff frequency
    # that starts low, sweeps up, then back down

    cutoff_sweep = Breakpoint.from_pairs(
        ("0%", 200.0),    # Start at 200 Hz
        ("30%", 2000.0),  # Sweep up to 2000 Hz
        ("70%", 2000.0),  # Hold at 2000 Hz
        ("100%", 200.0),  # Sweep back down to 200 Hz
        name="cutoff_sweep"
    )

    print(f"Cutoff frequency sweep: {cutoff_sweep}")
    print()

    # Create operation with the breakpoint parameter
    # (This is conceptual - the actual parameter name depends on the CDP tool)
    print("To use this in an operation:")
    print("""
    filter_op = custom_operation(
        name="filter_sweep",
        program="filter",
        mode="lopass",
        params=[cutoff_sweep]  # Pass the breakpoint as a parameter
    )

    pipeline = Pipeline()
    pipeline.add_operation(filter_op)
    pipeline.run("input.wav", "output.wav", verbose=True)
    """)

    print("With verbose=True, you'll see the breakpoint file being created")
    print("and its path being passed to the CDP command.")
    print()


def main():
    """Run all examples."""
    print("=" * 60)
    print("CDP Pipeline - Breakpoint Automation Examples")
    print("=" * 60)
    print()

    example_simple_breakpoint()
    example_helper_methods()
    example_with_operation()
    example_constant_vs_varying()
    example_absolute_times()
    example_real_world_usage()

    print("=" * 60)
    print("Key Points:")
    print("=" * 60)
    print("• Use regular numbers (5.0) for constant parameters")
    print("• Use Breakpoint for time-varying parameters")
    print("• Percentages are relative to input file duration")
    print("• Can mix percentages and absolute times")
    print("• Breakpoint files are created automatically")
    print("• Use verbose=True to see the breakpoint files being created")
    print("=" * 60)


if __name__ == "__main__":
    main()
