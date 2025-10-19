#!/usr/bin/env python3

"""
pseudocode:

    a bunch of functions that take a filename and return a filename (or something else)
    possibly with additional args
    list_of_output_files = wrap(func, list_of_input_files)

"""

import os
import re
import shutil
import sys

import click
import sh
from turtledemo.chaos import f

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
TMP_DIR = os.path.join(SCRIPT_DIR, "tmp")


def setup():
    shutil.rmtree(TMP_DIR, ignore_errors=True)
    os.makedirs(TMP_DIR)


@click.command()
@click.option('--leafsize', default=1, help='leaf size')
@click.option("--outfile", default=None, help="Output file", required=True)
@click.argument("input_filenames", nargs=-1, type=click.Path(exists=True), required=True)
def main(leafsize, outfile, input_filenames):
    num_chans = 0
    if len(input_filenames) < 2:
        click.echo("Error: You must provide at least two filenames.", err=True)
        sys.exit(1)
    chans = wrap(input_filenames, get_num_chans)
    if not len(set(chans)) == 1:
        click.echo("Error: All input files must have the same number of channels.", err=True)
        # just for now so my head does not hurt too much
        sys.exit(1)
    num_chans = chans[0]
    if num_chans > 2:
        click.echo("Error: Only mono and stereo files are supported.", err=True)
        sys.exit(1)
    setup()
    temp_input_files = wrap(input_filenames, copy_file)
    mono_files = []
    # an exception to the wrap pattern:
    if num_chans == 1:
        mono_files = temp_input_files
    elif num_chans == 2:
        for file in temp_input_files:
            mono_files.extend(split_into_mono(file))
    else:
        print("Unsupported number of channels")
        sys.exit(1)
    wrap(mono_files, analyze)
    combine_inputs = []
    combine_outputs = []
    if num_chans == 1:
        combine_inputs.append(wrap(mono_files, get_ana_file))
        combine_outputs.append(os.path.join(TMP_DIR, "combined_c0.ana"))
    elif num_chans == 2:
        for i in range(1, 3):
            tmp = [x for x in mono_files if x.endswith(f"_c{i}.wav")]
            combine_inputs.append(wrap(tmp, new_ext))
            combine_outputs.append(os.path.join(TMP_DIR, f"combined_c{i}.ana"))
        # combine_inputs.append(wrap(mono_files, get_ana_file, type=1))
        # combine_inputs.append(wrap(mono_files, get_ana_file, type=2))
        # combine_outputs.append(os.path.join(TMP_DIR, "combined_c1.ana"))
        # combine_outputs.append(os.path.join(TMP_DIR, "combined_c2.ana"))
    # another exception to the wrap pattern:
    synth_outputs = []
    # import IPython;IPython.embed()
    for idx, input in enumerate(combine_inputs):
        interleave(input, combine_outputs[idx], leafsize)
        synth_outputs.append(synth(combine_outputs[idx]))
    if num_chans == 1:
        shutil.copy(synth_outputs[0], outfile)
    elif num_chans == 2:
        final = os.path.join(TMP_DIR, "combined.wav")
        submix(synth_outputs, final)
        shutil.copy(final, outfile)
    print(f"Created {outfile}")


def submix(channel_files, outfile):
    "combine 2 mono files into a stereo file"
    assert len(channel_files) == 2
    sh.submix("interleave", *channel_files, outfile) # pyright: ignore
    return outfile

def synth(ana_file):
    outputfile = new_ext(ana_file, "wav")
    sh.pvoc("synth", ana_file, outputfile) # pyright: ignore
    return outputfile

def get_ana_file(input_file, type=0):
    """
    Takes a temp input wav file
    Returns the corresponding analysis file
    type = 0 means the input file is mono
    type = 1 means the input file is the left (channel 1) side of a stereo file
    type = 2 means the input file is the right (channel 2) side of a stereo file
    """
    if type == 0:
        return new_ext(input_file)
    elif type == 1:
        return new_ext(input_file)
    elif type == 2:
        return new_ext(input_file)
    else:
        print("Unsupported type")
        sys.exit(1)

def wrap(files, func,*args, **kwargs):
    out = []
    for file in files:
        out.append(func(file, *args, **kwargs))
    return out


def interleave(ana_files, outfile, leafsize):
    # combine interleave clalc_c1.ana platange_c1.ana combined.ana 1
    sh.combine("interleave", *ana_files, outfile, leafsize) # pyright: ignore
    return outfile

def new_ext(filename, ext="ana", before_ext=""):
    segs = filename.split(".")
    curr_ext = segs[-1]
    pat = re.compile(rf"\.{curr_ext}$")
    return pat.sub(f"{before_ext}.{ext}", filename)

def analyze(filename):
    ana_file = new_ext(filename)
    sh.pvoc("anal", "1", filename, ana_file) # pyright: ignore
    return ana_file

def copy_file(filename):
    shutil.copy(filename, TMP_DIR)
    return os.path.join(TMP_DIR, os.path.basename(filename))

def get_dir(filename):
    return os.path.dirname(filename) or os.getcwd()

def split_into_mono(filename):
    sh.housekeep("chans", "2", filename) # pyright: ignore
    out = []
    for i in range(1, 3):
        out.append(filename.replace(".wav", f"_c{i}.wav"))
    return out


def get_num_chans(filename):
    return int(sh.sfprops("-c", filename)) # pyright: ignore


if __name__ == "__main__":
    main()
    # split_into_mono("/Users/dandante/Library/Application Support/Rack2/recordings/apfel blossom.wav")
