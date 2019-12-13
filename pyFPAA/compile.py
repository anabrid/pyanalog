#!/usr/bin/env python3

"""
This is a compiler for programmable analog computers (FPAAs). It was written by SvenK in Dec 2019
for quickly approaching a testing infrastructure for the XBAR module for the Analog Paradigm M-1
analog computer.

The script requires a (lengthy) machine description, which encodes the computational parts
available and is quite similar to a machine library in VHDL. That file encodes especially the
hard-wired vs. configurable parts of the machine.
The actual program is then rather short and describes how the configurable computational parts
are connected with each other. It also specifies constant coefficients which are set with
digital potentiometers or other digital steering parameters.

The output of this script is a single line of text, which are mostly hexadecimal encoded
instructions together with command characters, all following the serial console protocol which
the HybridController of the machine expects (http://analogparadigm.com/downloads/hc_handbook.pdf).

In order to run this program, all you need is PyYAML to read the YAML files. If you want
to draw circuit plots, you need matplotlib.

See the README file for further information.
"""

# external dependencies, install with "pip install pyyaml"
# If you don't have pip, install pip with "easy_install pip"
import yaml # PyYAML

# Python-included
import sys, os, argparse, glob, pathlib
from math import ceil
from copy import deepcopy
from collections import OrderedDict, namedtuple, defaultdict
from pprint import pprint, pformat
from collections.abc import Iterable
from functools import reduce
from numbers     import Number

# Helper routines for simply nested dictionaries:
flatten_dict = lambda dct: dict(reduce(lambda a,b: a+b, [list(dict(k).items()) for k in dct.values()]))
filter_dict = lambda dct: { k:v for k,v in dct.items() if v }
# Map [{'I1':'a'},{'I2':'b'},...] -> [('I1','a'),('I2','b'),...]
Target = namedtuple("Target", ['part','pin'])
pin2tuple = lambda dct: [ Target(t,p) for (t,p) in dct.items() ][0]
pins2tuples = lambda pl: [ Target(t,p) for tp in pl for (t,p) in tp.items() ]
# no need for bitarray
bool2bin = lambda boolean: '1' if boolean else '0'
int2bin = lambda number: bin(number)[2:] # cutting away the 0b from 0b10101
boolList2BinString = lambda lst: ''.join(map(bool2bin, lst))
bitstring2bin = lambda s: int('0b'+s, base=2)

machines_from_list = True # choose Machines from current directory instead of providing YAML file

parser = argparse.ArgumentParser(description="A circuit synthesizer for the HyConAVR.", epilog=__doc__)#, formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument("-v", "--verbose", action="store_true", help="Be more verbose")
parser.add_argument("-d", "--debug", action="store_true", help="Be even more verbose (debug mode)")
parser.add_argument("-o", "--output", default="-", metavar="OUTPUT.txt", help="Put output string into file (default is '-' and means stdout)")
parser.add_argument("-p", "--plot", metavar="OUTPUT.pdf", help="Plot crossbar switch")
if machines_from_list:
    curdir = os.path.dirname(os.path.realpath(__file__))
    available_architectures = {pathlib.Path(fn).stem: fn for fn in glob.glob(curdir+"/*.yml")}
    parser.add_argument("-a", "--arch", choices=available_architectures.keys(), default=iter(available_architectures), help=f"Target machine architecture description (any YAML file in directory {curdir} is available as machine)") 
else:
    parser.add_argument("-a", "--arch", metavar="MACHINE.yml", help="Target machine architecture description")
parser.add_argument("circuit", metavar="CIRCUIT.yml", help="The YAML file holding the circuit description")
args = parser.parse_args()

info  = lambda *w,**kw: print(*w,**kw,file=sys.stderr) if args.verbose or args.debug else 1
debug = lambda *w,**kw: print(*w,**kw,file=sys.stderr) if args.debug else 1

chipout = open(args.output, "w") if args.output != "-" else sys.stdout
def write_chip(*w,**kw): print(*w,**kw,end="",file=chipout)

def yaml_load(fname):
    with open(fname, "r") as cfh:
        return yaml.load(cfh, Loader=yaml.SafeLoader) # may rise ScannerError

arch = yaml_load(args.arch if not machines_from_list else available_architectures[args.arch])
circuit = yaml_load(args.circuit)

info("Welcome to the HyConAVR.ino Program Compiler.")
info("Input program:", circuit['title'])
info("Target machine:", arch['title'])

debug("arch:")
debug(pformat(arch))
debug("-----------------------------------------------------")
debug("circuit:")
debug(pformat(circuit))
debug("-----------------------------------------------------")

assigned_parts_by_entity = filter_dict({
    entity: OrderedDict({ part: None for part,parch in arch['configurable_parts'].items()
        if parch['type']==entity and not 'cannot_be_allocated' in parch })
    for entity in arch['entities'].keys() })

# Determine mapping of part names (circuit -> arch)
for part, spec in circuit['program'].items():
    t = spec['type']
    if not t in arch['entities']:
        raise ValueError(f"Invalid type {t} for Part {part} in Netlist {args.circuit}. Available types for given architecture {args.arch} are: {arch['entities'].keys()}")
    assigned_parts = assigned_parts_by_entity[t]
    none_allocated_parts = [k for k,v in assigned_parts.items() if not v ]
    #import ipdb; ipdb.set_trace() 
    if len(none_allocated_parts) == 0:
        raise ValueError(f"Have used up all {len(assigned_parts)} parts of type {t} in architecture {args.arch}! Cannot allocate another one.")
    target = none_allocated_parts[0]
    info(f"Allocating Type {t}: Mapping circuit part {part} onto architecture part {target}")
    assigned_parts[target] = part

# Mapping from architectured parts to user-named parts (having also None's for unallocated parts)
assigned_parts = flatten_dict(assigned_parts_by_entity)
# Identity mapping for architectured parts
default_mapping = { k:k for k in arch['configurable_parts'].keys() }
# Extend the architectured parts with basically the nonallocable ones
arch2user = {**default_mapping, **assigned_parts}
user2arch = { v:k for k,v in arch2user.items() }

# Setup the wired circuit. In this dictionary, the parts are named as in
# the architecture and *not* as from the user view. Use arch2user to translate
# the user view, i.e. access like wired_circuit[arch2user[userpartname]]...
wired_circuit = deepcopy(arch['configurable_parts'])
for part in filter_dict(assigned_parts).keys():
    wired_circuit[part].update(circuit['program'][assigned_parts[part]])

def resolve_user_pin(item):
    """
    Excepts a user-named part and always returns an architecture part name.
    Expands something like 'M2' to {'M2':'o'}, i.e. part -> {part:signal},
    where the default signal is the first output signal.
    (Note: This is a closoure over wired_circuit in a pseudo-OOP fashion.)
    """
    if isinstance(item, str):
        item = user2arch[item]
        return {item: arch['entities'][wired_circuit[item]['type']]['output'][0]['name'] }
    elif (isinstance(item, dict) and len(item)==1):
        return { user2arch[k]: v for k,v in item.items() } # could also convert to Target() at this place
    elif isinstance(item, Number):
        return item
    else: raise ValueError(f"Malformed target notation: {item}")
    
def resolve_machine_pin(item):
    """
    Expects an architecture part name. Never comes in touch with user names.
    Expands something like 'M2' to {'M2':'o'}, i.e. part -> {part:signal},
    where the default signal is the first output signal.
    (Note: This is a closoure over wired_circuit in a pseudo-OOP fashion.)
    """
    if isinstance(item, str):
        return {item: arch['entities'][wired_circuit[item]['type']]['output'][0]['name'] }
    elif (isinstance(item, dict) and len(item)==1) or isinstance(item, Number):
        return item
    else: raise ValueError(f"Malformed target notation: {item}")

# Sweep over all configurable parts
for pname, part in wired_circuit.items():
    # Prepare for giving output information in next sweep
    part['output'] = defaultdict(list)

    if not 'input' in part:
        part['input'] = []

    reference = arch['entities'][part['type']]

    # ensure the inputs are dictionaries
    if isinstance(part['input'], list):
        new_input = {}
        for i, inputdesc in enumerate(reference['input']):
            if i < len(part['input']):
                new_input[ inputdesc['name'] ] = part['input'][i]
        part['input'] = new_input

    # fill up defaults
    for name, value in reference.get('default_inputs', {}).items():
        if name not in part['input']:
            part['input'][name] = value

    # Resolve variables (inteded for numerical values):
    if 'coefficients' in circuit:
        for name, target in part['input'].items():
            if isinstance(target, str) and target in circuit['coefficients'].keys():
                part['input'][name] = circuit['coefficients'][target]
                info(f"Resolving variable {target}={part['input'][name]} at architecture part {pname}/{name}")


    # Name implicit (first) output lines
    for name, target in part['input'].items():
        try:
            part['input'][name] = resolve_user_pin(target)
        except KeyError: # thrown by user2arch
            #debug(f"Will pass malformed user target '{target}' at users {pname} to next sweep")
            userdesc = f"Architecture part {pname} (User part {arch2user[pname]})"
            raise ValueError(f"{userdesc}, input {name}: Cannot understand {target}, certainly because it is nonexistent")
        #if isinstance(target, str):
        #    part['input'][name] = {target: arch['entities'][wired_circuit[target]['type']]['output'][0]['name'] }


# final sweep over all configurable parts:
for pname, part in wired_circuit.items():
    userdesc = f"Architecture part {pname} (User part {arch2user[pname]})"
    # Check wire types
    for name, target in part['input'].items():
        adesc = { dct['name']: dct for dct in arch['entities'][part['type']]['input'] }
        if not name in adesc:
            raise ValueError(f"{userdesc} constructs input line {name} which doesn't exist for type {part['type']}")
        adesc = adesc[name]
        if adesc['type'] == 'numeric' and not isinstance(target, Number):
            raise ValueError(f"{userdesc} requires a number, but {target} given. (Hint: Maybe you used an undefined variable)")
        if isinstance(target, dict):
            if len(target) > 1:
                raise ValueError(f"{userdesc} contains too many information. {target} given")
            (tpart,tline), = target.items()
            tpart_reference = {dct['name']:dct for dct in arch['entities'][wired_circuit[tpart]['type']]['output'] }
            if not tline in tpart_reference:
                usertarget = { arch2user[k]:v for k,v in target.items() }
                raise ValueError(f"{userdesc} wires to nonexisting target in input {target} (User provided {usertarget})")
            tpart_reference = tpart_reference[tline]
            if tpart_reference['type'] != adesc['type']:
                raise ValueError(f"I{userdesc}: Incompatible target line {name}. Required type: {tpart_reference['type']}, but lined to {adesc}")

            # Give output information, because we can.
            wired_circuit[tpart]['output'][tline].append({pname:name})

    # Check if everything is given
    missing_keys = set([i['name'] for i in arch['entities'][part['type']]['input']]) \
                   - set(part['input'].keys())
    if missing_keys:
        raise ValueError(f"{userdesc}: Too few input lines given: Missing keys {missing_keys}")

# really final sweep: Ensure nonused parts have no output
for pname, part in wired_circuit.items():
    if len(part['input']) == 0 and len(part['output']) > 0 and not 'cannot_be_allocated' in part:
        raise ValueError(f"{userdesc} has no input but is wired to {part['output']}. The universe will collapse into a black hole!")

# yay
#info("wired_circuit: ")
#info(pformat(wired_circuit))
#sys.exit(-1)


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
        raise ValueError(f"Digital potentiometer value {value} out of bounds")
    return int(round(value * 1023))


# Go over hardwired parts
for hwname, hw in arch['wired_parts'].items():
    if hw['type'] == "DPT24":
        # DPT24 Potentiometers
        assert len(hw['enumeration']) <= 24, "DPT24 has only 24 digital potentiometers"
        for port, t in enumerate(pins2tuples(map(resolve_machine_pin,hw['enumeration']))):
            value = normalize_potentiometer(wired_circuit[t.part]['input'][t.pin])
            info(f"DPT24@{hw['address']}: Storing value {'%4d'%value} at DPT port {port} (corresponding to {t.part}:{t.pin})")
            write("P", hw['address'], "%02X"%port, "%04d"%value)
    elif hw['type'] == 'HC':
        # Hybrid controller: DPTs (same code as DPT24)
        assert len(hw['dpt_enumeration']) <= 8, "HC has only eight digital potentiometers"
        for port, t in enumerate(pins2tuples(map(resolve_machine_pin,hw['dpt_enumeration']))):
            value = normalize_potentiometer(wired_circuit[t.part]['input'][t.pin])
            info(f"HC@{hw['address']}: Storing value {value:4} at DPT port {port} (corresponding to {t.part}:{t.pin})")
            write("P", hw['address'], "%02X"%port, "%04d"%value)
        # Hybrid controller: Digital output
        assert len(hw['digital_output']) <= 8, "HC has only eight digital outputs"
        for port, t in enumerate(pins2tuples(map(resolve_machine_pin,hw['digital_output']))):
            value = wired_circuit[t.part]['input'][t.pin]
            info(f"HC@{hw['address']}: Storing {value} at digital output port {port} (corresponding to {t.part}:{t.pin})")
            write("D" if value else "d", hw['address'], "%1d"%port)
    elif hw['type'] == 'XBAR':
        # XBAR matrix
        N,M = len(hw['output_rows']), len(hw['input_columns'])
        assert N==16 and M==16, "XBAR only implemented for 16x16"
        info(f"XBAR@{hw['address']}: Computing XBAR of size NxM={N}x{M}")
        cols = pins2tuples(map(resolve_machine_pin, hw['input_columns']))
        rows = pins2tuples(map(resolve_machine_pin, hw['output_rows']))
        #outputs = { pname: dict(part['output']) for pname,part in wired_circuit.items() }
        inputs = { pname: { line: pin2tuple(target) for line,target in part['input'].items()
                   if isinstance(target,dict) } #and not "None" in target } # filter out empty inputs
                   for pname,part in wired_circuit.items() }

        # The AD8113 enforces that there is only one connection per (output) row.
        # In other words: In the XBAR, an output line can be connected only to one input
        #   line, but an input line in the XBAR can connect up to 16 outputs.
        # This is realized by having an output row being encoded in only 4 bits instead of 16.

        boolean_matrix = [[ Target(ip,il) == inputs[op][ol] and op!="None" and ip!="None" for (ip,il) in cols] for (op,ol) in rows]
        row_bitstrings = list(map(boolList2BinString, boolean_matrix))
        row_numbers = [ row.index(True) if sum(row) else 0 for row in boolean_matrix ]
        row_active = [sum(row)==1 for row in boolean_matrix]
        row_bitstring = [ f"{num:04b}{active:b}" for num,active in zip(row_numbers, row_active) ]

        for i,(bitvec,num,active,bitvec2,(op,ol)) in enumerate(zip(row_bitstrings,row_numbers,row_active,row_bitstring,rows)):
            info(f"XBAR@{hw['address']}: Writing bitmatrix[{i:2}]:",
                 f"{bitvec}={num:2d}=0x{num:1x} -> {op}:{ol}       [sending {bitvec2}]" if active else
                 f"{bitvec} [output not enabled] [sending {bitvec2}]")

        if not all([sum(row) in (0,1) for row in boolean_matrix ]):
            raise ValueError("XBAR matrix is unsuitable. See info output for it's values. Only a maximum of one `True` bit per row allowed.")

        bitstring = "".join(row_bitstring)
        assert len(bitstring)==80, "XBAR bitstring has wrong length"
        bitstring_hex = "%040x" % int('0b'+bitstring, base=2)

        write("PREFIX_FOR_XBAR", hw['address'], bitstring_hex)
    else:
        raise ValueError(f"Wired part {hwname}: Don't know what to do with type {hw['type']}.")

if args.plot:
    info(f"Drawing the XBAR to {args.plot}...")

    import numpy as np
    import matplotlib as mpl
    import matplotlib.pyplot as plt
    if args.debug: plt.ion() # interactive plotting

    mpl.rcParams['font.family'] = ['monospace'] # default is sans-serif
    fig = plt.figure(figsize=[7.,7.5])
    ax = fig.gca()
    plt.xticks(np.arange(M), [ f'{part}:{pin}' for part,pin in cols ], rotation=30, ha="left")
    plt.yticks(np.arange(N), [ f'{part}:{pin}' for part,pin in rows ])
    
    ax.xaxis.tick_top()
    ax.yaxis.tick_right()
    ax.set_axisbelow(True) # grid in background
    ax.set_aspect(1)
    plt.grid()
    
    Y,X = np.where(np.array(boolean_matrix))
    plt.scatter(X,Y)
    
    plt.xlim(-1,M)
    plt.ylim(-1,N)
    ax.invert_yaxis()

    plt.title(f"XBAR for {circuit['title']}", y=1.18, fontweight="bold")
    plt.tight_layout()
    plt.subplots_adjust(top=0.82)

    plt.savefig(args.plot)
    
