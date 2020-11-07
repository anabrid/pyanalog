"""
The autosetup module of the hycon package is the python implementation of the
similar named feature of the Perl HyCon library.

It is used to setup a hybrid controller based from a YAML file which includes
a mapping from names to computing element and potentiometer addresses and
a problem description containing information about timing, potentiometer
values (coefficients) and a readout group of interest. It can also describe
the configuration of an XBAR module.

The idea of this YAML file is to describe the analog circuit as complete as
possible, to keep the steering hycon code in perl (or python, respectively)
short. Furthermore, it brings some kind of highlevel description of the
circuit, since many parts of the circuit are given names.

This idea is some intermediate idea to the pyFPAA code which I wrote. It can
be seen as an alternative high-level frontend to pyHyCon. Remember, the idiom
of pyHyCon is to provide only a lowest level API for interaction with the
hardware hybrid controller.

About the history of this code: Bernd started to write his auto-setup code
at 25-DEC-2019. I started to write my pyFPAA code at the same time. Roughly
one year later, where most of the time was spent at other stuff, I now port
parts of Bernds auto-setup code to python in order to be able to use the
same YAML files.
"""

from collections import namedtuple

from .HyCon import HyCon

class DotDict(dict):
    """small syntactic sugar: dot.notation access to dictionary attributes"""
    def __getattr__(*args):
        val = dict.get(*args)
        return DotDict(val) if type(val) is dict else val
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__ 

# This is tolen from ../fpaa/fpaa.py  . TODO: just import or so.
def yaml_load(fname):
    # external dependencies, install with "pip install pyyaml"
    # If you don't have pip, install pip with "easy_install pip"
    import yaml # PyYAML
    
    with open(fname, "r") as cfh:
        return yaml.load(cfh, Loader=yaml.SafeLoader) # may rise ScannerError

class PotentiometerAddress(namedtuple("PotentiometerAddress", ["address", "number"])):
    """
    Stores a potentiometer address, which is a tuple of a (typically hex-given) bus address
    of the hardware element and an element-internal number. Example:
    
    >>> a = PotentiometerAddress(0x200, 20)
    >>> b = PotentiometerAddress.fromText("0x200/20")
    >>> a == b
    True
    >>> a.address   # Don't forget that python standard numeric output is in decimal
    512
    >>> a.toText()
    '0x200/20'
    """
    
    @classmethod
    def fromText(cls, text):
        "Parses something like 0x200/2 to (0x200, 2)"
        if not isinstance(text,str) or text.count("/") != 1 or not "0x" in text:
            raise ValueError("'%s' doesn't look like a valid potentiometer address. Should be like 0x200/2", text)
        address,number = text.split("/")
        return cls(int(address,16), int(number,16))
    def toText(self):
        return "0x%x/%x" % (self.address,self.number)

def autosetup(hycon, conf, reset=True):
    """
    hycon is expected to be an instance of HyCon.
    conf is expected to be a dictionary.
    
    If you want to load from a YAML file, use the yaml_load function.
    
    TODO: XBAR support not yet implemented.
    """
    
    if not 'problem' in conf: raise ValueError("No problem section defined!")
    problem = DotDict(conf["problem"]) # syntactic sugar
    elements = DotDict(conf["elements"]) # syntactic sugar
    
    if reset: hycon.reset()
    
    if "times" in problem:
        # Should say somewhere that times are always in micro seconds
        if "ic" in problem.times: hycon.set_ic_time(problem.times.ic)
        if "op" in problem.times: hycon.set_op_time(problem.times.op)

    # Initial Conditions
    # TODO: Skipping here, because mainly used in XBAR-relevant code...
    #for element in problem.get("IC",[]): # aka is dict
    #    value = problem.IC[element]
    #    sign = (value < 0)
    #    number = ...

    try:
        # Set potentiometer values (coefficients):
        for name, value in problem.get("coefficients", {}).items():
            dp = PotentiometerAddress.fromText(elements[name])
            hycon.set_pt(dp.address, dp.number, value)

        # Define read out group if specified:s
        if "ro-group" in problem:
            addresses = list(map(elements.get, problem["ro-group"]))
            hycon.set_ro_group(addresses)
    except KeyError as e:
        raise KeyError("Unknown coefficient or computing element: '%s'. It is not part of the element map." % e)
        
    # Derive the required XBAR setup:
    #if (defined($self->{problem}) and defined($xbar_address)) {
    # TODO: Skipping here...


class AutoConfHyCon(HyCon):
    """
    Syntactic sugar to provide a "setup" method similar to the perl
    HyCon API.
    
    TODO: Should also provide other methods for high level value read
    and set access.
    """
    def setup(self, conf):
        if isinstance(conf, str): conf = yaml_load(conf)
        autosetup(self, conf)
