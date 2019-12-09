#!/usr/bin/env python3

# external dependencies:
import yaml # PyYAML

# Python-included
import sys, os, argparse, glob, pathlib
from math import ceil
from copy import deepcopy
from collections import OrderedDict
from pprint import pprint, pformat
from collections.abc import Iterable
from functools import reduce

# Helper routines for simply nested dictionaries:
flatten_dict = lambda dct: dict(reduce(lambda a,b: a+b, [list(dict(k).items()) for k in dct.values()]))
filter_dict = lambda dct: { k:v for k,v in dct.items() if v }
# no need for bitarray
boolList2BinString = lambda lst: ''.join(['1' if x else '0' for x in lst])
boolString2Bin = lambda s: int('0b'+s, base=2)

curdir = os.path.dirname(os.path.realpath(__file__))
available_architectures = {pathlib.Path(fn).stem: fn for fn in glob.glob(curdir+"/*.yml")}

parser = argparse.ArgumentParser(description="An experimental synthesizer for some FPAA chips")
parser.add_argument("-v", "--verbose", action="store_true", help="Be more verbose")
parser.add_argument("-a", "--arch", choices=available_architectures.keys(),
    default=iter(available_architectures), help="Target machine architecture description")
parser.add_argument("circuit", help="The YAML file holding the circuit description")
args = parser.parse_args()

if args.verbose:
    def info(*w,**kw): print(*w,**kw,file=sys.stderr)
else:
    def info(*w,**kw): pass

def write_chip(*w,**kw): print(*w,**kw,end="") # todo: file=...

def yaml_load(fname):
    with open(fname, "r") as cfh:
        return yaml.load(cfh, Loader=yaml.SafeLoader) # may rise ScannerError

arch = yaml_load(available_architectures[args.arch])
circuit = yaml_load(args.circuit)


info("arch:")
info(pformat(arch))
sys.exit(1)

assigned_parts_by_entity = filter_dict({
    entity: OrderedDict({ part: None for part,parch in arch['partlist'].items()
        if parch['type']==entity and not 'cannot_be_allocated' in parch })
    for entity in arch['entities'].keys() })

# Determine mapping of part names (circuit -> arch)
for part, spec in circuit['netlist'].items():
    t = spec['type']
    if not t in arch['entities']:
        raise ValueError(f"Invalid type {t} for Part {part} in Netlist {args.circuit}. Available types for given architecture {args.arch} are: {arch['entities']}")
    assigned_parts = assigned_parts_by_entity[t]
    none_allocated_parts = [k for k,v in assigned_parts.items() if not v ]
    #import ipdb; ipdb.set_trace() 
    if len(none_allocated_parts) == 0:
        raise ValueError(f"Have used up all {len(assigned_parts)} parts of type {t} in architecture {args.arch}! Cannot allocate another one.")
    target = none_allocated_parts[0]
    info(f"Allocating Type {t}: Mapping circuit part {part} onto architecture part {target}")
    assigned_parts[target] = part

assigned_parts = flatten_dict(assigned_parts_by_entity)

# Setup the wired circuit
wired_circuit = deepcopy(arch['partlist'])
for part in filter_dict(assigned_parts).keys():
    wired_circuit[part].update(circuit['netlist'][assigned_parts[part]])

# yay
info("wired_circuit: ")
info(pformat(wired_circuit))


def write(command_letter, address, *data):
    write_chip(command_letter)
    if not isinstance(address,int):
        raise ValueError("Need address as integer (may specify as 0x123)")
    write_chip("%X"%address)
    for d in data:
        write_chip(d)

def normalize_potentiometer(value):
    "Map a real value [0..1] to Potentiometer value [0..1023]"
    value = float(value)
    if value < 0 or value > 1:
        raise ValueError("Potentiometer value out of bounds")
    return int(round(value * 1023))

# DPT24 Potentiometers
for pot in arch['DPT24']:
    for part, part_config in pot['enumeration'].items():
        for variable, port in part_config.items():
            value = normalize_potentiometer(wired_circuit[part]['variables'][
                arch['entities'][wired_circuit[part]['type']]['variables'].index(variable)] )
            info(f"DPT24@{pot['adress']}: Writing {part}/{variable} = {value}")
            write("P", pot['adress'], "%02X"%port, "%04X"%value)
            # TODO: Check values, looks wrong so far! But code "runs"

# XBAR matrix
for xbar in arch['XBAR']:
    N,M = len(xbar['output_rows']), len(xbar['input_columns'])
    nbits, nbytes, nhexchars = N*M, ceil(N*M/8), ceil(N*M/8*2)
    info(f"XBAR@{xbar['adress']}: Writing bitmatrix of size NxM={N}x{M} ({nbits} bits = {nbytes} bytes = {nhexchars} in hex)")

    boolean_matrix = [ 
          [ pin in wired_circuit[pout]['input']
	    for pin in xbar['input_columns']
          ] for pout in xbar['output_rows']
    ]

    bit_row_vectors = list(map(boolList2BinString, boolean_matrix))
    bit_matrix = boolString2Bin("".join(bit_row_vectors))
    bit_matrix_string = ("%%0%dX"%nhexchars) % bit_matrix
    for i,(bitvec,pout) in enumerate(zip(bit_row_vectors,xbar['output_rows'])):
        info(f"XBAR@{xbar['adress']}: Writing bitmatrix[{i}]: {bitvec} -> {pout}")
    write("XFIXMEX", xbar['adress'], bit_matrix_string)

# Missing: On-Off-Information about outgoing lines of XBAR!
