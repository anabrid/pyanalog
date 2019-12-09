#!/usr/bin/env python3

# external dependencies:
import yaml # PyYAML

# Python-included
import sys, os, argparse, glob, pathlib
from copy import deepcopy
from collections import OrderedDict
from pprint import pprint
from collections.abc import Iterable

# Helper routines for simply nested dictionaries:
flatten_dict = lambda dct: dict(sum([list(dict(k).items()) for k in dct.values()], start=[]))
filter_dict = lambda dct: { k:v for k,v in dct.items() if v }

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
pprint(wired_circuit)

info("arch")
pprint(arch)

def write(command_letter, address, data):
    write_chip(command_letter)
    if not isinstance(address,int):
        raise ValueError("Need address as integer (may specify as 0x123)")
    write_chip("%X"%address)
    if not isinstance(data, Iterable):
        data = [data]
    for d in data:
        if not isinstance(d,int):
            raise ValueError("Want to write numbers")
        write_chip("%X"%d)

# DPT24 Potentiometers
for pot in arch['DPT24']:
    for part,  pot['enumeration'].items()

    # TODO Normalization: Potentiometers have value between 0 .. 1023 !!
    write("P", pot['address'], number, value)

