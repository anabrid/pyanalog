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
    
    >>> a = PotentiometerAddress(0x200, 0x20)
    >>> b = PotentiometerAddress.fromText("0x200/20")  # FIXME: Is number really base 16?
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

def autoconnect(conf):
    """
    Opens a file handle to the target position found in the YAML file. Follows the same
    rules as the perl routine, i.e. looks for *serial* or *tcp* key and connects
    according to the parameters.
    
    Example serial port configuration:
    
    ::
        serial:
          port: /dev/cu.usbserial-DN050L21
          bits: 8
          baud: 250000
          parity: none
          stopbits: 1
          poll_interval: 10
          poll_attempts: 20000
          
    Note that we only take into account port and baud rate, since everything else looks standard
    and the pySerial port cannot deal with an integer stopbit ``1`` but expects something like ``serial.STOPBITS_ONE``.
    As a note to the future, https://tools.ietf.org/html/rfc2217.html is supported by pySerial and
    should be adopted by the YAML definition.,
    
    Example TCP port configuration:
    
    ::
        tcp:
            addr: 192.168.31.190
            port: 12345
            connection_timeout: 2
            timeout: 0.1
            poll_interval: 10
            poll_attempts: 2000
            quick_start: False
            
    Again, we only take into account the IP address and the TCP port, everything else is ignored for the
    time being.
    """
    import connections
    
    c = DotDict(conf)
    if 'tcp' in c:
        return connections.tcpsocket(c.tcp.addr, c.tcp.portr)
    elif 'serial' in conf:
        return connections.serial(c.serial.port, c.serial.baud)
    else:
        raise ValueError("Could neither find `tcp` nor `serial` section in configuration. Available keys: {list(c)}")
    

class AutoConfHyCon(HyCon):
    """
    Syntactic sugar to provide a "setup" method similar to the perl
    HyCon API.
    
    TODO: Should also provide other methods for high level value read
    and set access.
    
    ``conf`` can either be a string holding the YAML filename  or a dictionary (holding the
    configuration content, i.e. parsed YAML file).
    """
    def __init__(self, conf):
        if isinstance(conf, str):
            conf = yaml_load(conf)
        fh = autoconnect(conf)
        super().__init__(self, fh)
        self.setup(conf)
    
    def setup(self, conf):
        "Will store conf as DotDict for easier later access"
        self.conf = DotDict(yaml_load(conf) if isinstance(conf, str) else conf)
        autosetup(self, self.conf)
        
    def get_data_by_name(self):
        "Get readout group data handily labeled by name"
        if not "ro-group" in self.conf.problem: raise ValueError("No Read-out group defined")
        data = self.get_data() # shape (sample_points, readout_group_length)
        return { name: [line[i] for line in data] for i,name in enumerate(self.conf.problem["ro-group"]) }
    
    def set_pt_by_name(self, name, value):
        "Set a digital potentiometer by name"
        dp = PotentiometerAddress.fromText(self.conf.elements[name])
        return self.set_pt(dp.address, dp.number, value)
    
