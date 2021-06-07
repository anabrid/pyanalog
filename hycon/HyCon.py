#!/usr/bin/env python3
#
# Copyright (c) 2020 anabrid GmbH
# Contact: https://www.anabrid.com/licensing/
#
# This file is part of the HyCon module of the PyAnalog toolkit.
#
# ANABRID_BEGIN_LICENSE:GPL
# Commercial License Usage
# Licensees holding valid commercial anabrid licenses may use this file in
# accordance with the commercial license agreement provided with the
# Software or, alternatively, in accordance with the terms contained in
# a written agreement between you and Anabrid GmbH. For licensing terms
# and conditions see https://www.anabrid.com/licensing. For further
# information use the contact form at https://www.anabrid.com/contact.
# 
# GNU General Public License Usage
# Alternatively, this file may be used under the terms of the GNU 
# General Public License version 3 as published by the Free Software
# Foundation and appearing in the file LICENSE.GPL3 included in the
# packaging of this file. Please review the following information to
# ensure the GNU General Public License version 3 requirements
# will be met: https://www.gnu.org/licenses/gpl-3.0.html.
# For Germany, additional rules exist. Please consult /LICENSE.DE
# for further agreements.
# ANABRID_END_LICENSE
#

"""
PyHyCon -- a Python Hybrid Controller interface.

Note that the IO::HyCon Perl 5 module is the reference implementation
that is maintained by the HyConAVR firmware author (Bernd). You can find
the IO::HyCon Perl module at https://metacpan.org/pod/IO::HyCon

While this implementation tries to be API-compatible with the reference
implementation, it tries to be minimal/low-level and won't implement any
client-side luxury (such as address mapping). It is the task of the
user to implement something high-level ontop of this.

Especially, the following tasks are implemented by different modules which
can but do not needed to be used:

* Connection managament: HyCon just assumes a file handle, but different
  connection types are proposed in the :mod:`connections` module.
* Autosetup: PyHyCon is plain python and has no dependency, for instance 
  on YAML. There is :mod:`autosetup` which implements the "autosetup"
  functionality of Perl-HyCon.
* High level functionality is implemented on top of HyCon and not within.
  See for instance :cls:`fpaa.fpaa` for an abstraction which can generate
  HyCon instructions and is aware of the circuit design at the same time.
  
The hycon module also includes an interpreter for the HyCon serial stream
"protocol". See :mod:`replay` for further details.

Logging and Debugging
^^^^^^^^^^^^^^^^^^^^^

There are several ways to inspect what HyCon is doing. One of the simplest
is to activate logging on ``INFO`` level:

>>> import logging
>>> logging.basicConfig(level=logging.INFO)
>>> # proceed here as usual, i.e.: hc = HyCon(...)

"""

# All these modules are Python internals
import sys, re, logging, time
from collections import namedtuple
from copy import deepcopy

#logging.basicConfig(level=logging.INFO) # only for testing
log = logging.getLogger('HyCon') # or __name__

def ensure(var, **q):
    """
    This is our assert function which is used widely over the code for dynamic
    parameter checking. ``q`` stands for *query*. The function will return
    silently if the query is fullfilled and raise a ``ValueError`` otherwise.
    Examples for success:
    
    >>> ensure(42, eq=42)
    >>> ensure("foo bar", re="fo+.*")
    >>> ensure(17, inrange=(0,20))
    >>> ensure("x", within="xyz")
    >>> ensure("bla", length=3)
    >>> ensure("blub", isa=str, length=4, re="b.*")
    
    And in case of failure:
    >>> ensure(3, within=[1,2,9])
    Traceback (most recent call last):
    ...
    ValueError: Got var=3, but it is none of [1, 2, 9].
    """
    # Should probably use inspect.stack() or traceback.extract_stack() to get original varname
    basemsg=f"Got {var=}" if not 'basemsg' in q else q['basemsg']
    if 'eq' in q and not var == q['eq']: raise ValueError(f"{basemsg}, but should be '{q['eq']}'")
    if 're' in q and not re.match(q['re'], var): raise ValueError(f"{basemsg}, but that doesn't match regexp '{q['re']}'")
    if 'inrange' in q and not (var >= q['inrange'][0] and var <= q['inrange'][1]): raise ValueError(f"{basemsg}, but it is not in range{q['inrange']}.")
    if 'within' in q and not var in q['within']: raise ValueError(f"{basemsg}, but it is none of {q['within']}.")
    if 'length' in q and not len(var)==q['length']: raise ValueError(f"{basemsg}, of {len(var)=} but expected to be len(var)={q['length']}.")
    if 'isa' in q and not isinstance(var, q['isa']): raise ValueError(f"{basemsg}, which is of {type(var)=} but expected  type {q['isa']}.")

class expect:
    """
    ``ensure`` delayed and on stereoids: Can be initialized with a ``query`` (but with
    further options) and then called with a ``HyConRequest``. Will check the *response*
    and also allows *return value mapping*, for instance with regexpes or by splitting.
    Example:
    
    >>> R = HyConRequest("dummy")
    >>> R.response = "1,2,3"
    >>> E = expect(split=",", type=int)
    >>> print(list(E(R)))
    [1, 2, 3]
    """
    def __init__(self, **q): self.q=q
    def __call__(self, r): # r: HyConRequest
        q = deepcopy(self.q);
        q['basemsg'] = f"Unexpected response: Command {r.command} yielded '{r.response}'"
        ensure(r.response, **q)
        mapper = q['type'] if 'type' in q else lambda x:x # id
        try:
            if 'ret' in q: return mapper(re.match(q['re'], r.response).groupdict()[ q['ret'] ])
            if 'split' in q: return map(mapper, re.split(q['split'], r.response))
            if 're' in q and not 'type' in q: return re.match(q['re'], r.response)
            return mapper(r.response)
        except ValueError:  raise ValueError(f"{basemsg} but cannot be casted/mapped to {mapper}")
    def __str__(self): return "expect(%s)"%str(self.q)[1:-1].replace("'",'')

def wont_implement(reason):
    "Will not implement: Returns a function which raises ``NotImplementedError(reason)`` when called."
    def not_implemented(*v,**kw): raise NotImplementedError(reason)
    not_implemented.__doc__ = f"*Not implemented* because {reason}"
    return not_implemented

class HyConRequest:
    """
    A HyConRequest models a single *request* and *response* cycle. It stores the ASCII ``command``
    emitted by the HyCon and can save a *expected response* future/promise (see ``expect`` class).
    A HyConRequest can only be made once. If you want to do it several times, you have to (deep)
    copy the instance.
    """
    def __init__(self, command, expected_response=None):
        self.executed = False
        self.command = command
        self.expected_response = expect(re=expected_response) if isinstance(expected_response, str) else expected_response
        
    def __str__(self):
        return f"HyConRequest({self.command}, {self.expected_response}, {self.executed=}, "+\
            f"response={self.response if hasattr(self, 'response') else 'n.a.'}, "+\
            f"reply={self.reply if hasattr(self, 'reply') else 'n.a.'})"
    
    __repr__ = __str__
        
    def write(self, hycon):
        "Run this request. Can only be executed once. Can be chained."
        if self.executed:
            raise ValueError("Shall not execute same command twice.")
        self.executed = True
        log.info(f"Sending [{self.command}]")
        hycon.fh.write(self.command)
        return self # chainable
    
    def read(self, hycon, expected_response=None, read_again=False):
        "Read response from HyCon. If *read_again* is given, will read several times. Can be chained."
        if not expected_response: expected_response = self.expected_response
        if hycon.unidirectional:
            log.debug("Unidirectional channel, skipping reading from HyCon...")
            return self # chainable
        if not expected_response:
            log.debug("No response expected, skipping reading from HyCon...")
            return self # chainable
        log.debug(f"Waiting for response {expected_response} ... ")
        if read_again or not hasattr(self, "response"):
            self.response = hycon.fh.readline().strip() # Note: The HyConAVR always answers with a full line.
        if not self.response:
            raise ValueError(f"No Response from Hybrid controller! Command was '{self.command}'")
        self.reply = expected_response(self) # "Reply" is the highlevel, mapped answer
        return self # always chainable


class HyCon:
    """
    Low-Level Hybrid Controller OOP interface, similar to the Perl Hybrid controller.
    
    This is a minimalistic implementation which tries to implement all neccessary checking
    of input/output request/reply structure correctness, but won't do any *high level*
    support for applications. Users are assumed to write such code on themselves. The PyFPAA
    library is an example for a high level "frontend" against HyCon, which includes a
    circuit understanding, etc.
    """
    
    DIGITAL_OUTPUT_PORTS = 8
    DIGITAL_INPUT_PORTS = 8
    DPT_RESOLUTION = 10
    DPT_MAX_INT_VALUE = (2 ** DPT_RESOLUTION - 1)  # 0 <= value <= 1023
    XBAR_CONFIG_BYTES = 10
    MAX_RO_GROUP_SIZE = 500 # hardcoded in HyConAVR.ino
    
    def __init__(self, fh, unidirectional=False):
        """
        Expects fh to be an IOHandler. This could be an open file,
        a (unix/inet) domain socket, a special device (serial port),
        some serial port library, etc.
        
        .. note:: We expect the `fh` to have an API compatible to
            `ABC.IOBase <https://docs.python.org/3/library/io.html>`_. The two methods
            `fh.readline()` and `fh.write()` are required. You find some example "polyfills"
            in the :mod:`connections` module.
        
        Make sure you disable output buffering (on print/write to fh), since commands do
        not end with newlines. Responses from the uC always end with newlines.
        
        If unidirectional is set, PyHyCon won't try to read from fh. Any
        read checks and mappings will be skipped and HyConRequest.read()
        will always return None.
        
        Important: We don't send anything at construction time, unless the
        reference implementation. Call reset() on yourself if you feel to do
        so.
        """
        self.fh = fh
        self.unidirectional = unidirectional
        if unidirectional: log.info(f"Won't make any attempt to read from the HyCon at {fh}")
    
    def query(self, *args, **kwargs):
        "Create a request, run it and check the reply"
        return HyConRequest(*args, **kwargs).write(self).read(self)
    
    def command(*args, help=None, **kwargs):
        "Return a method which, when called, creates a request, runs it and checks the reply"
        method = lambda self: self.query(*args, **kwargs)
        method.__doc__ = help
        return method
    
    ic               = command('i', '^IC',            help="Switch AC to IC-mode")
    op               = command('o', '^OP',            help="Switch AC to OP-mode")
    halt             = command('h', '^HALT',          help="Switch AC to HALT-mode")
    disable_ovl_halt = command('a', '^OVLH=DISABLED', help="Disable HALT-on-overflow")
    enable_ovl_halt  = command('A', '^OVLH=ENABLED',  help="Enable HALT-on-overflow")
    disable_ext_halt = command('b', '^EXTH=DISABLED', help="Disable external HALT")
    enable_ext_halt  = command('B', '^EXTH=ENABLED',  help="Enable external HALT")
    repetitive_run   = command('e', '^REP-MODE',      help="Switch to RepOp")
    single_run       = command('E', '^SINGLE-RUN',    help="One IC-OP-HALT-cycle")
    pot_set          = command('S', '^PS',            help="Activate POTSET-mode")


    def repeated_reset(self):
        from .connections import repeated_reset
        repeated_reset(self.fh)
        
    def single_run_sync(self):
        "Synchronous run (finishes after a single run finished). Return value is true if terminated by ext. halt condition"
        q = self.query('F', '^SINGLE-RUN')
        timeout = 1.1 * (self.ictime + self.optime) # raises error if set_ic_time/set_op_time not called before
        log.info(f"Waiting for single run sync to finish for {timeout} ms...")
        time.sleep(timeout / 1000)  # converting timeout (microseconds) to seconds
        res = q.read(self, expect(re='^EOSR(HLT)?'), read_again=True)
        was_terminated_by_ext_halt_condition = res.reply.groups()[0]=="HLT" # EOSRHLT
        return was_terminated_by_ext_halt_condition
    
    def set_ic_time(self, ictime):
        "Sets IC (initial condition) time in MILLISECONDS."
        ensure(ictime, within=range(0,999999)); self.ictime = ictime
        return self.query('C%06d' % ictime, expect(eq=f"T_IC={ictime}"))
    
    def set_op_time(self, optime):
        "Sets OP (operation mode) time in MILLISECONDS"
        ensure(optime, inrange=(0,999999)); self.optime = optime
        return self.query('c%06d' % optime, expect(eq=f"T_OP={optime}"))
    
    def get_data(self):
        "Supposed to be called when a read out group is defined and the machine is in (synchronous) OP mode. "
        q = self.query('l', "^No data!|.*$")
        if q.response == "No data!": return None
        data = []
        while True:
            resp = q.read(self, expect(re=r"^([-\d\.\s]*|EOD)*$"), read_again=True).response.split()
            if "EOD" in resp: break
            data.append(list(map(float, resp)))
        return data
    
    def read_element_by_address(self, address):
        "Read any machine element voltage. Expecting 16-bit element address as integer."
        ensure(address, isa=int)
        response_match = self.query("g%04X" % address, r"(?P<value>.+)\s+(?P<id>.+)").reply
        return response_match.groupdict() # return the dictionary value-> ..., id-> ..., caveat, should be all numeric!?
    
    def set_ro_group(self, addresses):
        "Defines a read out group, expects addresses to be an integer list of 16-bit element addresses."
        ensure(len(addresses), inrange=(1,5*self.MAX_RO_GROUP_SIZE))
        for a in addresses: ensure(a, isa=int)
        return self.query("G" + ";".join([f"{a:04X}" for a in addresses]) + ".")
    
    read_ro_group = command('f', expect(split=";", type=float), help="Query for currently set read out group")
    read_digital = command("R", expect(re="^"+r"\d\s"*(DIGITAL_INPUT_PORTS-1), split='', type=bool), help="Read digital inputs")
    
    def digital_output(self, port, state):
        "Set digital output pins of the Hybrid Controller"
        ensure(port, inrange=(0, self.DIGITAL_OUTPUT_PORTS)); ensure(state, isa=bool)
        return self.query(f"{'D' if state else 'd'}{port:1d}")

    def set_xbar(self, address, config):
        """Exactly {self.XBAR_CONFIG_BYTES*2} HEX-nibbles are required to config data."""
        ensure(address, isa=int); ensure(config, length=self.XBAR_CONFIG_BYTES*2)
        return self.query(f"X{address:04X}{config}", expect(eq="XBAR READY"))
    
    read_mpts = wont_implement("because it is just a high-level function which calls pot_set and iterates a list of potentiometer address/names.")
    
    def set_pt(self, address, number, value):
        "Set a digital potentiometer by address/number."
        ensure(value, inrange=(0,1))
        value = int(value * self.DPT_MAX_INT_VALUE) # 0000 <= value <= 1023
        return self.query(f"P{address:04X}{number:02X}{value:04d}", expect(eq=f"P{address:X}.{number:X}={value:d}"))
    
    def read_dpts(self):
        """
        Asks the Hybridcontroller for reading out *all* DPTs in the machine (also DPT24 modules).
        Returns mapping of PT module to list of values in that module.
        """
        response = self.query("q", '.*,.*').reply.string
        # strings looks like:
        #{'200': '204,44,244,102,89,244,89,639,639,1023,1023,1023,639,639,1023,1023,1023,300,300,79,79,102,102,300',
        # '300': '0,0,0,0,0,0,0,306'} 
        # numbers is the same parsed as hex/int.
        strings = dict([ items.split(":") for items in response.strip().split(";") ])
        numbers = { int(k, base=16): list(map(int, v.split(","))) for k,v in strings.items() }
        dpt2float = lambda val: val / 2**self.DPT_RESOLUTION
        floats = { k: list(map(dpt2float, v)) for k,v in numbers.items() }
        return floats
    
    def get_status(self):
        "Queries the HybridController about it's current status. Will return a dictionary."
        response = self.query('s', '.*=.*,.*').reply.string # expecting something with commas :-)
        state = dict(items.split("=") for items in response.split(","))
        state['RO-GROUP'] = state['RO-GROUP'].split(";")
        state['DPTADDR'] = state['DPTADDR'].split(";") # don't resolve mapping
        return state

    get_op_time = command('t', expect(re=r"t_OP=(?P<time>-?\d*)", ret='time', type=float), help="Asks about current OP time")
    reset = command('x', expect(eq='RESET'), help="Resets the HybridController (has no effect on python instance itself)")

    

