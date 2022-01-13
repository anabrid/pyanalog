#!/usr/bin/env python3

"""
Pythonic API for Siglent Digital Oscilloscope in order to perform data aquisition.
This is a python standalone code implementing the SCPI protocol (without further
Python libraries) over sockets. The connection is assumed to be established over
Ethernet (not USB, despite this should also work, in principle, as the siglent
registers as UART device over USB). The code can work in blocking and non-blocking
fashion (but is not fully async).

See the programming guide
https://siglentna.com/wp-content/uploads/dlm_uploads/2021/01/SDS1000-SeriesSDS2000XSDS2000X-E_ProgrammingGuide_PG01-E02D.pdf
for the reference. This code was tested against an Siglent SDS1104X-E with four 10bit channels.

Here is a picture of such an oscilloscope. On the back, it has an RJ45 ethernet
connector and a USB client socket. Whether over USB-UART or TCP, it allows to be
programmed with the
`Standards Commands for Programmable Instruments (SCPI) <https://en.wikipedia.org/wiki/Standard_Commands_for_Programmable_Instruments>`_
standard, which is basically a simple command-reply text protocol similar to the
one we implement with the :class:`hycon.HyCon`.

.. image:: https://www.welectron.com/media/image/product/9607/lg/siglent-sds1104x-e-oszilloskop~3.jpg
   :width: 80%
   :alt: Photo of Siglent

Over ethernet, one can also access the oscilloscope screen via
`VNC <https://en.wikipedia.org/wiki/Virtual_Network_Computing>`_. 
The oscilloscope provides a web interface which includes an in-browser
VNC client and models the interface controls. Both is shown side on side in
the UI. The interface knobs are translated to SCPI commands via Javascript.
The status indicators are polled. The overall UI is quite heavy, rather slow
and generates, in particular, high load on the oscilloscope.

.. image:: https://www.eevblog.com/forum/testgear/siglent-sds1104x-e-in-depth-review/?action=dlattach;attach=438190;image
   :width: 100%
   :alt: Screenshot of Web Interface

.. warning::

    Make sure you **never ever run the browser interface at the same time as 
    a telnet session or this script**. This will break the oscilloscope randomly
    and requires you to cold start it. This is a reproducable bug in the Siglent
    firmware.
    
    It is, however, fine to run a VNC connection to the oscilloscope while
    running this script.
    
This script is also executable as standalone and offers an API to contact the siglent
and do a single readout, assuming the triggering took place independently.
"""

import socket, time, re, numpy as np, sys, argparse

# TODO: Improve logging
log = lambda *a,**b: print(*a,**b,file=sys.stderr)

def downsample(data, factor):
    """
    Downsample all numpy 1d arrays, since ``query("MEMORY_SIZE 70K")`` has no effect...
    TODO: MEMSIZE only works in STOP mode.
    """
    return { k: v[::factor] for k,v in data.items() }


class siglent:
    """
    This is a classy API to the oscilloscope. A usage example intermixed with
    HyCon controlling may look like this:
    
    .. code-block:: python
    
       import hycon.aquisition.siglent_scpi as sig
       
       hc = AutoConfHyCon("something.yml")
       print(hc.get_status())
       
       siglent = sig.siglent("192.168.32.68")
       print("Siglent Status: ", siglent.status())
       
       hc.ic()
       print("ICs freely running, preparing Siglent trigger...")
       #input("Press enter to continue")
       prepped = siglent.trigger_single()
       siglent.log("Siglent Status: ", siglent.status())
       if not prepped:
           raise ValueError("Could not properly prepare the Siglent.")
       time.sleep(1)
       hc.single_run_sync()
       time.sleep(2) # 2 seconds "OP time".
       print("Finished with single run sync. Waiting another second for siglent.")
       time.sleep(1)
       hc.ic()
       #input("HC stopped. Press enter to readout siglent.")
       data = siglent.read_all()
       sig.write_npz(data, f"output.npz")
    
    .. warning::
    
       While this code basically works, the refactoring at PyAnalog-introduction
       time was not tested. That is, this code is not yet fully tested.

    """
    
    def send(self, md, log_end="\n", blocking=False, sleep_sec=0.5):
        "Send SCPI command to siglent."
        if blocking:
            # to ensure the oscilloscope is finished with the command...
            if not query("*OPC?", sleep_sec=0) == "1":
                raise ValueError("OPC before blocking send did not return 1")
        binary = (cmd + "\n").encode("ascii")
        log("SCPI> ", cmd, end=log_end, flush=True)
        sent_len = self.s.send(binary)
        time.sleep(sleep_sec) # 1sec suggested by the programming examples...
        if len(binary) != sent_len:
            log(f"Tried to send {len(binary)} bytes but could send only {sent_len}.")
        if blocking:
            # to ensure the oscilloscope is finished with the command...
            if not query("*OPC?", sleep_sec=0) == "1":
                raise ValueError("OPC after blocking send did not return 1")

    def query(cmd, sleep_sec=0.5):
        """
        Query the siglent for something.
        This is basically a :meth:`send`/:meth:`recv` cycle, according to the
        SCPI standard.
        """
        send(cmd, log_end="", sleep_sec=sleep_sec)
        return s.recv(self.bufsize).decode("ascii", "ignore").strip() # ignore binary non-decodable

    def query_num(cmd, pat):
        "A shorthand which returns the number in some readout which looks like ``a = 123``."
        r = query(cmd, sleep_sec=0) # we never experienced race conditions here, so don't sleep
        readout = float(re.match(pat, r).group(1))
        log(" = ",readout)
        return readout
    
    def __init__(self, host, port=5025):
        """
        This class connects to SCPI Raw TCP, so use port 5025 instead of Telnet 5024.
        Insert the IPv4 address (or resolvable domain, or IPv6) of the SIGLENT oscilloscope
        as string, for instance as in ``osci = siglent("192.168.32.68")``. It is
        passed to ``socket.connect()``.
        """
        
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Try out if TCP_NODELAY improves something.
        s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

        address = (host, port)
        s.connect(address)
        log("SCPI Raw TCP Py3 Socket reader connected to ", target)

        self.bufsize = 4 * 1024 # bytes
        self.channels = list(range(1,5))

        # first check whether we can work
        log("= ", query("*IDN?"))

        run_full_setup = True
        if run_full_setup:
            send("*RST", blocking=True)

            send("stop", blocking=True) # attention, STOP seems to reset the oscilloscope :-(

            # Correctly setup for aquiring 4 channels and so on
            for c in self.channels:
                send(f"C{c}:TRACE ON", blocking=True)
                send(f"C{c}:VDIV 1V", blocking=True)

            send("tdiv 100ms", blocking=True)

            # set memory size *after* setting the number of channels.
            # choices: 7k, 70k, 700k, 7M
            send("MEMORY_SIZE 70K", blocking=True) # only works in STOP mode.
            log(" = ", query("MEMORY_SIZE?"))
            # ALSO: query("TRIG_DELAY -600ms") is reasonable with 100ms time division


        # TODO: all this could be encapsuled within a class.

        self.vdiv = { c: query_num("c%d:vdiv?"%c, "C%d:VDIV ([\d\.E+-]*)V"%c) for c in self.channels }
        self.ofst = { c: query_num("c%d:ofst?"%c, "C%d:OFST ([\d\.E+-]*)V"%c) for c in self.channels }
        self.tdiv = query_num("tdiv?", "TDIV ([\d\.E+-]*)S")
        self.sara = query_num("sara?", "SARA ([\d\.E+-]*)Sa/s")

    def status(self):
        """
        Reads out the status bit (``INR?``) and translates it according to the manual,
        thus returning a string.
        
        .. warning::
        
           Attention, Querying INR? is *NOT* a read-only operation but changes
           the oscilloscope status.
        """
        value = self.query("INR?")
        try:
            value = int(value.split()[-1]) # "INR 0" -> int("0")
        except ValueError:
            raise ValueError(f"Expected INR status msg but got {value=}")
        # hint: INR only returns bit 0 and bit 13...
        bits = [
            "15 Not used (always 0)",
            "14 Not used (always 0)",
            "Trigger is ready", # bit 13
            "Pass/Fail test detected desired outcome",
            "Waveform processing has terminated in Trace D",
            "Waveform processing has terminated in Trace C",
            "Waveform processing has terminated in Trace B",
            "Waveform processing has terminated in Trace A",
            "A memory card, floppy or hard disk exchange has been detected",
            "Memory card, floppy or hard disk has become full in “AutoStore Fill” mode",
            "5 Not use(always 0)",
            "A segment of a sequence waveform has been acquired",
            "A time-out has occurred in a data block transfer",
            "A return to the local state is detected",
            "A screen dump has terminated",
            "A new signal has been acquired" # bit 0
        ]
        meanings = [ desc for i,desc in enumerate(bits[::-1]) if value & (2**i) ]
        if not meanings:
            meanings = ["Zero"]
        return meanings


    def trigger_single(self):
        """
        Brings the Oscilloscope in single trig mode and checks the success of this
        operation (returns ``True`` in case of passed check).
        """
        #send("STOP", blocking=True) # somehow this resets the oscilloscope...
        print("I do *not* stop or so. Just asking for trigger mode single...")
        self.send("TRIG_MODE SINGLE", blocking=True)
        q = self.query("TRIG_MODE?")
        log(" = ",q)
        
        # Again, wait wait wait, why not wait a bit more? The oscilloscope otherwise
        # doesn't catch up...
        time.sleep(1)
        if not self.query("*OPC?") == "1":
            raise ValueError("OPC before blocking send did not return 1")
        
        return q == "TRMD SINGLE"
        """
        inr = query("INR?")
        if inr == "INR 8193":
            inr = query("INR?")
        if inr != "INR 0":
            log(f"Cannot ARM, since {inr=} but expected 0")
            return False
        else:
            log("=", query("ARM")) # ARM is send only, not query
            return True
        """

    def read_wf(self, channel, try_multiples=2):
        """
        Read the actual waveform. This can be called after an aquisition took place
        and the oscilloscope trigger fired. In many times, this will fail and return
        no data. This results in a thrown ``ValueError``. Otherwise, data recieving
        is looped (with lot's of logging since it takes some seconds). When some 
        consistency is reached (all announced data is recieved), will return the 
        *raw recieved channel data* as 1d list of numbers. That is, these are 10bit
        numbers.
        
        This function will by default try several times to ask for data, in case the
        siglent did not properly answer.
        """
        assert channel in self.channels
        
        # Wait until for instance some slow data aquisition is finished
        if not self.query("*OPC?") == "1":
            raise ValueError("OPC before blocking send did not return 1")
        
        self.send("c%d:wf? dat2" % channel, log_end="")
        data = s.recv(bufsize)
        log(" = ", data[:25], "...")
        prefix = "Channel %d | " % channel
        log(prefix, f"Read (first) {len(data)} bytes.")
        
        if(not data):
            raise ValueError("Did not recieve any data.")

        # parse data format, begins like "C1:WF DAT2,#9007000000\x1e...."
        ascii_reply = data.decode("ascii", "ignore") # ignore binary non-decodable
        try:
            num_digits_idx = ascii_reply.find("#")
            num_digits = int(ascii_reply[num_digits_idx+1])
            num_bytes = int(ascii_reply[num_digits_idx+2:num_digits_idx+2+num_digits])
        except ValueError as e:
            print(f"Channel {channel}: Error at parsing data, Full reply is {ascii_reply=}")
            if try_multiples:
                print(f"Trying again for {try_multiples-1} attempts...")
                return self.read_wf(channel, try_multiples - 1)
            else:
                raise e
            
        start_payload_idx = num_digits_idx+2+num_digits

        # byte array that will grow
        all_data = data[start_payload_idx:]
        
        if not num_bytes:
            print(f"Got a zero answer ({num_bytes=}). Input was {ascii_reply=}")
            if try_multiples:
                print(f"Trying again for {try_multiples-1} attempts...")
                return self.read_wf(channel, try_multiples - 1)
            else:
                raise ValueError("Could not read any data (got 0 length).")

        log(prefix, "Recieved %9d / %d bytes (%.2f%%)" % (len(all_data), num_bytes, len(all_data)/num_bytes*100))

        # now loop until all data are recieved:
        while len(all_data) < num_bytes:
            data = s.recv(self.bufsize)
            all_data += data
            log(prefix, "Recieved %9d / %d bytes (%.2f%%)" % (len(all_data), num_bytes, len(all_data)/num_bytes*100))

        return all_data

    def read_all(self, channels=None):
        """
        Read the actual waveforms by querying the passed channel list. A channel is
        an integer between ``0`` and ``4``, see ``siglent.channels`` for the valid
        channel list. If not provided, all channels are read.
        
        Will do the conversion to voltages, that is, returns proper floats representing
        a voltage in unit V.  Returns a dictionary mapping the channel name to the 1d data.
        """
        if not channels: channels = self.channels
        channel_data = { d: self.read_wf(d) for d in self.channels }

        log("Finished reading channels:")
        for k,v in channel_data.items(): log(f"{k}: {len(v)} entries ({type(v)})")
        data_len = len(channel_data[next(iter(channel_data))])
        assert all([data_len == len(v) for k,v in channel_data.items() ]), "Non-uniform data recieved."

        log("Conversion to voltages...")
        def adc2volt(channel):
            unsigned = channel_data[channel]
            #signed = np.array([ (256-d if d > 127 else d) for d in unsigned])
            
            signed = np.frombuffer(unsigned, dtype=np.uint8).astype(np.int16)
            signed[signed > 127] = signed[signed > 127] - 256

            weird_factor = 25 # comes from documentation!
            volt = signed / weird_factor * self.vdiv[channel] - self.ofst[channel]
            
            # unfortunately, computing with floats blows up the data size in bytes
            # a lot. We basically still only have 8 bit Resolution. Floating point
            # single precision is 32 bit. Numpy supports half precision, thought
            # (16bit). Some modern numpy's also support quad precision (8bit).
            volt = volt.astype(np.float16)
            return volt

        # voltages in volt
        data = { f"channel{k}_volt": adc2volt(k) for k,v in channel_data.items() }

        # time axis in seconds
        weird_factor = 14/2
        time = -self.tdiv * weird_factor + np.arange(data_len) / self.sara
        
        data["time_sec"] = time
        
        return data

def write_npz(data, fname=None):
    """
    Write out NPZ files. See https://numpy.org/doc/stable/reference/generated/numpy.savez.html
    for this numpy specific binary file format.
    Expects data to be a python dictionary (ideally some ``np.array``).
    """
    if not fname and not sys.stdout.isatty():
        log("Writing compressed .npz file to stdout...")
        target = sys.stdout.buffer # sys.stdout does not accept binary, .buffer does.
    elif not fname:
        log("Stdout is a Terminal, writing to output.npz.")
        log("Hint: Call like ./scpi-socket.py > target.npz for other target.")
        target = open("output.npz", "wb")
    else:
        log(f"Writing npz file to {fname}...")
        target = open(fname, "wb")
        
    np.savez_compressed(target, **data) # writes binary

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Make a read swipe on a Siglent oscilloscope and write to stdout.")
    parser.add_argument("--host", help="Host/IP address of siglent")
    args = parser.parse_args()
    siglent = siglent(args.host)
    write_npz(siglent.read_all())
 
