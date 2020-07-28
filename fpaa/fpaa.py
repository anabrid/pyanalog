#!/usr/bin/env python3

# Python-included
import sys, os, argparse, glob, logging
from math import ceil
from copy import deepcopy
from collections import OrderedDict, namedtuple, defaultdict
from pprint import pprint, pformat
from collections.abc import Iterable
from pathlib import Path
from functools import reduce
from numbers import Number

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

def chunks(lst, n):
    for i in range(0, len(lst),n):
        yield lst[i:i+n]

module = __file__
log = logging.getLogger(module)

info = log.info
debug = log.debug

machines_from_list = True # choose Machines from current directory instead of providing YAML file

def yaml_load(fname):
    # external dependencies, install with "pip install pyyaml"
    # If you don't have pip, install pip with "easy_install pip"
    import yaml # PyYAML
    
    with open(fname, "r") as cfh:
        return yaml.load(cfh, Loader=yaml.SafeLoader) # may rise ScannerError


architectures_basedir = os.path.dirname(os.path.realpath(__file__))
available_architectures = {Path(fn).stem: fn for fn in glob.glob(architectures_basedir+"/*.yml")}

def load_from_yaml(circuit, arch):
    """
    Expects arch and circuit to be strings.
    """
    if not Path(arch).is_file():
        if arch in available_architectures:
            arch = available_architectures[arch]
        else:
            raise ValueError(f"{arch} is neither a file nor a registered architecture.")
    arch = yaml_load(arch)
    circuit = yaml_load(circuit)
    return (circuit, arch)

def synthesize(circuit, arch):
    """
    Translate a circuit to a netlist for a given target architecture.
    
    This routine is the heart of the FPAA compiler. It mainly
    
    * Allocates available hardware to the requested ones by the user circuits
      and allows for book keeping between the user named and architecture named computing
      components.
    * Ensures consistency of the resulting circuit (there are no dangling wires,
      no over-allocation, etc.)
      
    There is a lot of *info* and *debug* output available if turned on via Python
    logging.
    
    Expects ``arch`` and ``circuit`` to be nested data structures (dicts and lists holding
    strings and numbers), similar to their YAML representation. The documentation does
    not yet cover an in-depth description of these data structures, but there are tons
    of example YAML files which are straightforward to understand.
    
    Returns ``wired_circuit``, a list of computing components (which itself are again
    "PODs", i.e. dicts with nested data structures).
    """

    info("Welcome to the HyConAVR.ino Program Compiler.")
    info("Input program: "  + circuit['title'])
    info("Target machine: " + arch['title'])

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
            raise ValueError(f"Invalid type {t} for Part {part} in Netlist {circuit['title']}. Available types for given architecture {arch['title']} are: {', '.join(arch['entities'].keys())}")
        assigned_parts = assigned_parts_by_entity[t]
        none_allocated_parts = [k for k,v in assigned_parts.items() if not v ]
        #import ipdb; ipdb.set_trace() 
        if len(none_allocated_parts) == 0:
            raise ValueError(f"Have used up all {len(assigned_parts)} parts of type {t} in architecture {arch['title']}! Cannot allocate another one.")
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
    # Note that arch2user is not always invertible. Several arch parts could
    # not be used and resolve to None.

    # Setup the wired circuit. In this dictionary, the parts are named as in
    # the architecture and *not* as from the user view. Use arch2user to translate
    # the user view, i.e. access like wired_circuit[arch2user[userpartname]]...
    wired_circuit = deepcopy(arch['configurable_parts'])
    for part in filter_dict(assigned_parts).keys():
        wired_circuit[part].update(circuit['program'][assigned_parts[part]])

    def resolve_user_pin(item): # closure over arch
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

    # As a service, for the time being, provide the readout/measurement positions as info
    if "observables" in circuit:
        for var, utarget in circuit["observables"].items():
            (tpart,tline), = resolve_user_pin(utarget).items()
            try: address = arch["configurable_parts"][tpart]['address'][tline]
            except KeyError:
                # should check before if tpart actually has output named tline.
                raise ValueError(f"At requesting output for {var}: Archtecture missing address for output line {tline} in part {tpart} in section configurable_parts")
            info(f"Observable {var} (user defined part {utarget}) can be measured at architecture part output {tpart}:{tline}, adress 0x{address:04x}")

    # yay
    #info("wired_circuit: ")
    #info(pformat(wired_circuit))
    #sys.exit(-1)
    return wired_circuit


def normalize_potentiometer(value, resolution_bits=10):
    "Map a real value [0..1] to Potentiometer value [0..1023]"
    maxval = 2**resolution_bits - 1 # 2**10-1 = 1023
    value = float(value)
    if value < 0 or value > 1:
        raise ValueError(f"Digital potentiometer value {value} out of bounds")
    return int(round(value * maxval))

last_seen_xbars = [] # an ugly global, filled by compile_instructions; for later plotting

def compile_instructions(wired_circuit, arch):
    """
    Compile a netlist (``wired_circuit``) to configuration *instructions* for setting
    up the analog computer hybrid controller.
    
    This routine basically loops over the *hardwired parts* of the given architecture,
    i.e. built-in
    
    * potentiometers (DPT-24 and HC)
    * cross bar arrays (XBAR)
    
    and configures them according to the given wired_circuit. This means that relevant
    allocated potentiometers will be set and the XBAR configuration bitmask will be
    computed from the hardware description provided by the circuit and the architecture.
    
    Currently returns a list of instructions (tuples) which could be directly be written
    out to serial or passed to PyHyCon.
    
    .. note::
       This method will change in near time and talk directly to a PyHyCon instance.
    """
    instructions = []

    # should actually call write(tpl) or directly PyHyCon
    instruct = lambda *tpl: instructions.append(tpl)

    def resolve_machine_pin(item): # closure over arch
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

    # Go over hardwired parts
    for hwname, hw in arch['wired_parts'].items():
        if hw['type'] == "DPT24":
            # DPT24 Potentiometers
            assert len(hw['enumeration']) <= 24, "DPT24 has only 24 digital potentiometers"
            for port, t in enumerate(pins2tuples(map(resolve_machine_pin,hw['enumeration']))):
                numeric_value = wired_circuit[t.part]['input'][t.pin]
                normalized_value = normalize_potentiometer(numeric_value)
                info(f"DPT24@{hw['address']:x}: Storing value {'%4d'%normalized_value} at DPT port {port:2} (corresponding to {t.part}:{t.pin})")
                #print(f'$ac->set_pt("DPT24-{port}", {numeric_value});')
                instruct("P", hw['address'], "%02X"%port, "%04d"%normalized_value)
        elif hw['type'] == 'HC':
            # Hybrid controller: DPTs (same code as DPT24)
            assert len(hw['dpt_enumeration']) <= 8, "HC has only eight digital potentiometers"
            for port, t in enumerate(pins2tuples(map(resolve_machine_pin,hw['dpt_enumeration']))):
                numeric_value = wired_circuit[t.part]['input'][t.pin]
                normalized_value = normalize_potentiometer(numeric_value)
                info(f"HC@{hw['address']:x}: Storing value {normalized_value:4} at DPT port {port:2} (corresponding to {t.part}:{t.pin})")
                instruct("P", hw['address'], "%02X"%port, "%04d"%normalized_value)
                #print(f'$ac->set_pt("HCDPT-{port}", {numeric_value});')
            # Hybrid controller: Digital output
            assert len(hw['digital_output']) <= 8, "HC has only eight digital outputs"
            for port, t in enumerate(pins2tuples(map(resolve_machine_pin,hw['digital_output']))):
                value = wired_circuit[t.part]['input'][t.pin]
                info(f"HC@{hw['address']:x}: Storing {value} at digital output port {port} (corresponding to {t.part}:{t.pin})")
                instruct("D" if value else "d", hw['address'], "%1d"%port)
                #print(f'$ac->digital_output({port}, %d);' % (1 if value else 0))
        elif hw['type'] == 'XBAR':
            # XBAR matrix
            N,M = len(hw['output_rows']), len(hw['input_columns'])
            assert N==16 and M==16, "XBAR only implemented for 16x16"
            info(f"XBAR@{hw['address']:x}: Computing XBAR of size NxM={N}x{M}")
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

            boolean_matrix = [[ ol in inputs[op] and Target(ip,il) == inputs[op][ol] and op!="None" and ip!="None" for (ip,il) in cols] for (op,ol) in rows]
            row_bitstrings = list(map(boolList2BinString, boolean_matrix))
            row_numbers = [ row.index(True) if sum(row) else 0 for row in boolean_matrix ]
            row_active = [sum(row)==1 for row in boolean_matrix]
            row_bitstring = [ f"{active:b}{num:04b}" for num,active in zip(row_numbers, row_active) ]
                    
            for i,(bitvec,num,active,bitvec2,(op,ol)) in enumerate(zip(row_bitstrings,row_numbers,row_active,row_bitstring,rows)):
                info(f"XBAR@{hw['address']:x}: Writing bitmatrix[row {i:2}]:",
                    f"{bitvec}={num:2d}=0x{num:1x} -> {op}:{ol}       [sending {bitvec2}]" if active else
                    f"{bitvec} [output not enabled] [sending {bitvec2}]")

            if not all([sum(row) in (0,1) for row in boolean_matrix ]):
                raise ValueError("XBAR matrix is unsuitable. See info output for it's values. Only a maximum of one `True` bit per row allowed.")
            
            last_seen_xbars.append( (cols,rows,boolean_matrix) ) # for later plotting...

            # Caveat 1: Chip expects rows in order row15...row0
            # Caveat 2: Don't try to convert a bitstring of length 80 to a single int, it will overflow.
            bitstring = "".join(row_bitstring[::-1])
            assert len(bitstring)==80, "XBAR bitstring has wrong length"
            bitstring_hex = "".join(["%02X"%int(x, base=2) for x in chunks( "".join(row_bitstring[::-1]), 8)])
            info(f"Bitstream to send ({len(bitstring)} characters): {bitstring}")
            info(f"Hextream  to send ({len(bitstring_hex)} characters): {bitstring_hex}")
            instruct("X", hw['address'], bitstring_hex)
            #print(f"$ac->set_xbar('XBAR16', '{bitstring_hex}');")
        else:
            raise ValueError(f"Wired part {hwname}: Don't know what to do with type {hw['type']}.")
        
    return instructions

def plot_xbar(target_file, circuit_title, xbar_config=None, interactive_plotting=False):
    """
    Draw an the allocation of a crossbar switch array (xbar) matrix.
    
    xbar_config is a tuple with (cols,rows,boolean_matrix), and by default the last one
    from a global registry (last_seen_xbars) is taken, which is what you want.
    """
    info(f"Drawing the XBAR to {target_file}...")
    (cols,rows,boolean_matrix) = xbar_config if xbar_config else last_seen_xbars[-1]
    M,N = 16,16

    import numpy as np
    import matplotlib as mpl
    import matplotlib.pyplot as plt
    if interactive_plotting: plt.ion()

    mpl.rcParams['font.family'] = ['monospace'] # default is sans-serif
    fig = plt.figure(figsize=[7.,7.5])
    ax = fig.gca()
    plt.xticks(np.arange(M), [ f'{i} ({part}:{pin})' for i,(part,pin) in enumerate(cols) ], rotation=30, ha="left")
    plt.yticks(np.arange(N), [ f'{i} ({part}:{pin})' for i,(part,pin) in enumerate(rows) ])
    
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

    plt.title(f"XBAR for {circuit_title}", y=1.18, fontweight="bold")
    plt.tight_layout()
    plt.subplots_adjust(top=0.82)

    plt.savefig(target_file)
    
def cli():
    """
    This module is callable via ``python -m fpaa`` or ``./fpaa.py``. It exposes the main
    functions on the command line which is especially helpful for debugging or
    interactively programming an analog computer from the command line.

    Call ``--help`` for all possible command line options.
    """
    parser = argparse.ArgumentParser(description="A circuit synthesizer for the HyConAVR.", epilog=__doc__)#, formatter_class=argparse.RawTextHelpFormatter
    parser.add_argument("-v", "--verbose", dest="verbose_count",
                        action="count", default=0,
                        help="increases log verbosity for each occurence.")
    parser.add_argument("-o", "--output", default="-", metavar="OUTPUT.txt", help="Put output string into file (default is '-' and means stdout)")
    parser.add_argument("-p", "--plot", metavar="OUTPUT.pdf", help="Plot crossbar switch")
    
    arch_group = parser.add_mutually_exclusive_group(required=True)
    arch_group.add_argument("-A", "--registered-arch", choices=available_architectures.keys(), default="AP-M1-Mini", help=f"Target machine architecture description: Any YAML file in directory {architectures_basedir} is available as machine") 
    arch_group.add_argument("-a", "--arch", metavar="path/to/my/MACHINE.yml", help="Target machine architecture description (any valid filename)")
    
    parser.add_argument("circuit", metavar="CIRCUIT.yml", help="The YAML file holding the circuit description")
    args = parser.parse_args()
    
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG,
                        format='%(name)s (%(levelname)s): %(message)s')
    # Sets log level to WARN going more verbose for each new -v.
    log.setLevel(max(3 - args.verbose_count, 0) * 10)
    
    chipout = open(args.output, "w") if args.output != "-" else sys.stdout
    
    circuit, arch = load_from_yaml(args.circuit, args.arch or args.registered_arch)
    wired_circuit = synthesize(circuit, arch)
    instructions = compile_instructions(wired_circuit, arch)
    
    # That was used for raw writing once. Could just write map(write, instructions).
    # However, we want to use the HyCon interface anyway in the future, so this code
    # will be superseded.
    def write(command_letter, address, *data):
        if not isinstance(address,int):
            raise ValueError("Need address as integer (may specify as 0x123)")
        command = f"{command_letter}{address:04X}" + "".join(data)
        debug(f"Writing out: {command}")
        print(command, file=chipout)
    
    
    print(instructions)

    if args.plot:
        plot_xbar(args.plot, circuit_title=circuit['title'])#, interactive_plotting=args.debug)
    
if __name__ == "__main__":
    try:
        cli()
    except Exception as e:
        log.error(e)  # will show stack trace only
        sys.exit(-1)  # when at least one -v is given.
    
