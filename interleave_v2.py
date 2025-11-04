#!/usr/bin/env python3

"""
Reimplementation of interleave.py using the cdp_pipeline library.

This demonstrates how the new library simplifies the original workflow.
"""

import sys
import click
from cdp_pipeline import Pipeline
from cdp_pipeline.operations import combine_interleave


@click.command()
@click.option("--leafsize", default=1, help="Leaf size for interleaving")
@click.option("--outfile", help="Output file", required=True)
@click.option("--keep-temp", is_flag=True, help="Keep temporary files for debugging")
@click.option("--verbose", is_flag=True, help="Print CDP commands as they are executed")
@click.argument(
    "input_filenames", nargs=-1, type=click.Path(exists=True), required=True
)
def main(leafsize, outfile, keep_temp, verbose, input_filenames):
    """Interleave multiple audio files using CDP's combine interleave."""

    if len(input_filenames) < 2:
        click.echo("Error: You must provide at least two filenames.", err=True)
        sys.exit(1)

    # Create pipeline with single operation
    pipeline = Pipeline()
    pipeline.add_operation(combine_interleave(leafsize=leafsize))

    try:
        # Run pipeline - it handles all the complexity:
        # - Splitting stereo to mono
        # - Converting WAV to ANA
        # - Running combine interleave per channel
        # - Converting ANA back to WAV
        # - Merging mono channels to stereo
        result = pipeline.run(
            input_files=list(input_filenames),
            output_file=outfile,
            keep_temp=keep_temp,
            verbose=verbose,
        )

        click.echo(f"Created {result.path}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
