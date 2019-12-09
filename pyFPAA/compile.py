#!/usr/bin/env python3

# external dependencies:
import yaml # PyYAML

# Python-included
import sys, os, argparse, glob, pathlib

curdir = os.path.dirname(os.path.realpath(__file__))
available_architectures = {pathlib.Path(fn).stem: fn for fn in glob.glob(curdir+"/*.yml")}

parser = argparse.ArgumentParser(description="An experimental synthesizer for some FPAA chips")
parser.add_argument("-a", "--arch", choices=available_architectures.keys(),
    default=iter(available_architectures), help="Target machine architecture description")
parser.add_argument("circuit", help="The YAML file holding the circuit description")
args = parser.parse_args()

with open(circuit, "r") as cfh:
    c = yaml.load(cfh, Loader=yaml.SafeLoader) # may rise ScannerError

print(c)
