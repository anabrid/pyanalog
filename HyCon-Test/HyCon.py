"""
PyHyCon -- a Python Hybrid Controller interface.

Note that the IO::HyCon perl module is the reference implementation
that is maintained by the HyConAVR firmware author (Bernd).

While this implementation tries to be API-compatible with the reference
implementation, it tries to be minimal/low-level and won't implement any
client-side luxury (such as address mapping). It is the task of the
user to implement something high-level ontop of this.
"""

def expect(**q): #eq=None, re=None, split=None, as=None):
    def response_matcher(r):
        basemsg = f"Unexpected response: Command {r.command} yielded '{r.response}'"
        # 1. Checkers
        if 'eq' in q and not r.response == q['eq']:
            raise ValueError(f"{basemsg} but should give '{q['eq']}'")
        if 're' in q and not re.match(q['re'], r.response):
            raise ValueError(f"{basemsg} but that doesnt match regexp '{q['re']}'")
        # 2. Mappers
        mapper = q['as'] if 'as' in q else lambda x:x # id
        try:
            if 'ret' in q: return mapper(re.match(q['re'], r.response).groupdict()[ q['ret'] ])
            if 'split' in q: return map(mapper, re.split(q['split'], r.response))
            return mapper(r.response)
        except ValueError:  raise ValueError(f"{basemsg} but cannot be casted/mapped to {mapper}")
    response_matcher.__str__="response_matcher(%s)"%str(q)
    return response_matcher

def wont_implement(reason):
    def not_implemented(*v,**kw): raise NotImplementedError(reason)
    not_implemented.__doc__ = f"Not implemented because {reason}"
    return not_implemented

# naming aka HTTP: Query consists of Request and Response?
class HyConRequest:
    def __init__(self, command, expected_response=None):
        self.executed = False
        self.command = command
        self.expected_response = expect(re=expected_response) if isinstance(expected_response, str) else expected_response
        
    def write(self, hycon):
        if self.executed:
            raise ValueError("Shall not execute same command twice.")
        self.executed = True
        hycon.fh.write(command)
        return self # chainable
    
    def read(self, hycon, read_again=False):
        "Returns matching (can be None or re.Match object"
        # The HyConAVR always answers with a full line.
        print(f"... waiting for response {response} ... ")
        if read_again or not hasattr(self, "response"):
            self.response = hycon.fh.readline()
        if not self.response:
            raise ValueError(f"No Response from Hybrid controller! Command was '{self.command}'")
        return self.expected_response(self.response) # provides mapping and check


class HyCon:
    DIGITAL_OUTPUT_PORTS = 8
    DIGITAL_INPUT_PORTS = 8
    DPT_RESOLUTION = 10
    XBAR_CONFIG_BYTES = 10
    
    def __init__(self, fh):
        """
        Expects fh to be an IOHandler. This could be an open file,
        a (unix/inet) domain socket, a special device (serial port),
        some serial port library, etc.
        """
        self.fh = fh
    
    def query(self, command, expected_response=None):
        return HyConRequest(key, expected_response).write(self).read(self)
    
    def command(key, resp_pattern=None, *args, help=None):
        method = lambda: query(self, key, *args, resp_pattern)
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

    def single_run_sync(self):
        q = query('F', '^SINGLE-RUN')
        timeout = 1.1 * (self.times['ic_time'] + self.times['op_time'])
        res = q.read('^EOSR(HLT)?', read_again=True)
        was_terminated_by_ext_halt_condition = res.groups()[0]=="HLT" # EOSRHLT
        return was_terminated_by_ext_halt_condition
    
    def set_ic_time(self, ictime):
        assert ictime in range(0,999999)
        return query('C%06d' % ictime, expect(eq=f"T_IC={ictime}"))
    
    def set_op_time(self, optime):
        assert optime in range(0,999999)
        return query('c%06d' % optime, expect(eq=f"T_OP={optime}"))
    
    def read_element_by_address(self, address):
        ensure(isinstance(address, int), "Expecting 16-bit address as integer")
        response_match = query("g%04X" % address).match_response(r"(?P<value>.+)\s+(?P<id>.+)")
        return response_match.groupdict() # return the dictionary value-> ..., id-> ..., caveat, should be all numeric!?
    
    def set_ro_group(self, addresses):
        # What about address formatting, as well as hex or int?
        query("G" + ";".join(hex(addresses)))
    
    read_ro_group = command('f', expect(split=";", type=float))
    read_digital = command("R", expect(re="^"+"\d\s"*(HyCon.DIGITAL_INPUT_PORTS-1), split='', type=bool), help="Read digital inputs")
    
    # Q: Does this reset the Readout group on the HyConAVR?
    # because of line $self->{'RO-GROUP'} = [];
    def digital_output(self, port, state):
        "Set digital output pins of the Hybrid Controller"
        ensure(port in range(0, DIGITAL_OUTPUT_PORTS)); ensure(state in [True, False])
        query(f"{'D' if state else 'd'}{port:04X}")

    def set_xbar(self, address, config):
        ensure(isinstance(address, int), "XBAR address must be given as integer")
        ensure(len(config)==self.XBAR_CONFIG_BYTES*2,
            f"Exactly {self.XBAR_CONFIG_BYTES*2} HEX-nibbles are required to config data. {len(config)} found.")
        query("X{address:04X}{config}", expect(eq="XBAR READY"))
    
    read_mpts = wont_implement("because it is just a high-level function which calls pot_set and iterates a list of potentiometer address/names.")
    
    def set_pt(self, address, number, value):
        "Set a digital potentiometer by address/number."
        ensure(value >= 0 and value <= 1, "Value must be >= 0 and <= 1")
        value = int(value * (2 ** self.DPT_RESOLUTION - 1)) # 0000 <= value <= 1023
        input = (address, number, value)
        output = query(f"P{address:04X}{number:02X}{value:04d}").match_response("^P([^.]+)\.([^=]+)=(\d+)$").groups()
        ensure(all([i==o for i,o in zip(input,output)], f"Set_PT failed, input was {input} but output is {output}")
    
    read_dpts = wont_implement("because it doesn't actually query the hardware but just ask the HC about its internal storage.")
    
    def get_status(self):
        response = query('s')
        state = { k:v for items.split("=") for items in response.split(",") }
        state['RO-GROUP'] = state['RO-GROUP'].split(";")
        state['DPTADDR'] = state['DPTADDR'].split(";") # don't resolve mapping

    get_op_time = command('t', expect(re="t_OP=(?P<time>-?\d*)", ret='time', to=float))
    reset = command('x', expect(eq='RESET'))
    
