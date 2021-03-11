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
# ANABRID_END_LICENSE
#

"""
Connection or "backends" for the PyHyCon.

The :cls:`HyCon.HyCon` class requires a file handle to be passed. Usually, file
APIs are cursed in many languages (also python), but you can get your way out
with the following examples and also classes in this module.

Tested or "proven" connection interfaces are:

* :cls:`tcpsocket`: A small adapter for the :meth:`socket` python builtin.
* :cls:`human`: A small dummy adapter which prints to the interactive user terminal session
  and expects commands from there (the naming is ironically pointing to the human acting as
  actual Hybrid controller hardware endpoint).

Somewhat experimental but known to work is especially for unidirectional access:

* :cls:`StringIO.StringIO`: Circumventing file access by reading from/to strings.
* :cls:`sys.stdout` for just dumping HyCon-generated instructions

We expect `PySerial <https://pythonhosted.org/pyserial/>`_ to work without needing this module.

Usage Examples
--------------

The following examples are suitable to be run in an interactive python REPL to explore
the APIs.

Using PyHyCon with a microcontroller "simulator"
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

>>> ac = HyCon(serialdummy())                                                                                            
>>> ac.set_ic_time(1234)                                  # doctest: +SKIP                                                                                  
<< Sending [C001234] to uC
[type reply of uC]>> T_IC=1234
HyConRequest(C001234, expect(eq: T_IC=1234), self.executed=True, response=T_IC=1234, reply=T_IC=1234)

Using PyHyCon only for writing firmware commands
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    
>>> ac = HyCon(sys.stdout, unidirectional=True)
>>> ac.set_ic_time(234)
C000234HyConRequest(C000234, expect(eq: T_IC=234), self.executed=True, response=n.a., reply=n.a.)

Such a unidirectional approach can be interesting when generating bitstreams, for
larger integration tests, etc.

Using PyHyCon over TCP/IP
^^^^^^^^^^^^^^^^^^^^^^^^^

>>> sock = tcpsocket("localhost", 12345)                 # doctest: +SKIP
>>> ac = HyCon(sock)                                     # doctest: +SKIP
>>> ac.reset()                                           # doctest: +SKIP
>>> ac.digital_output(3, True)                           # doctest: +SKIP
>>> ac.set_op_time(123)                                  # doctest: +SKIP
>>> ac.set_xbar(0x0040, "0000000210840000781B")          # doctest: +SKIP

This setup is particularly interesting when connecting network-transparently to
actual hardware. The target TCP server is expected to route the contents to a
serial port/USB UART without introducing buffering. Examples for this kind of
stub servers are given at networking-hc_.

Using PyHyCon over Serial
^^^^^^^^^^^^^^^^^^^^^^^^^

>>> fh = serial("/dev/ttyUSB0", 115200)                     # doctest: +SKIP
>>> ac = HyCon(fh)                                          # doctest: +SKIP
>>> ac.digital_output(3, True)                              # doctest: +SKIP
>>> # etc.

You are encouraged to use the :cls:`serial` class, which uses
`PySerial <https://pythonhosted.org/pyserial/>`_ under the hood and does the
clearing/resetting of the stream for you (something which is more cumbersome over serial
then over TCP).

If you really want, you can also use PySerial directly:

>>> import Serial from serial                               # doctest: +SKIP
>>> fh = Serial("/dev/ttyUSB0", 115200)                     # doctest: +SKIP
>>> ac = HyCon(fh)                                          # doctest: +SKIP

Note that this approach suffers from binary/string conversions, but you could
probably wrap ``open(fh)`` in some text mode.

If you (also) do not like PySerial, you can connect to a char device on a unixoid
operating system with vanilla python (this example is kind-of-untested):

>>> import os
>>> fd = os.open("/dev/ttyUSB0", os.O_RDWR | os.O_NOCTTY)      # doctest: +SKIP
>>> fh = os.fdopen(self.fd, "wb+", buffering=0)                # doctest: +SKIP
>>> ac = HyCon(fh)                                             # doctest: +SKIP

In this case, you certainly want to set the connection parameters (baud rate, etc.) by
``ioctl``, for instance in before on your linux terminal using a command
like ``stty -F /dev/ttyUSB0 115200``, or with ``stty ospeed 115200``
and ``stty ispeed 115200`` on Mac. Furthermore, when using this approach, consider
writing a small wrapper which runs ``fh.flush()`` after writing.
"""

import logging

class human:
    "Dummy IOWrapper for testing HyCon.py without the actual hardware"
    def write(self, sth):      print(f"<< Sending [{sth}] to uC")
    def readline(self): return input("[type reply of uC]>> ")

class tcpsocket:
    "Wrapper for communicating with HyCon over TCP/IP. See also HyCon-over-TCP.README for further instructions"
    def __init__(self, host, port):
        from socket import socket # builtin
        log = logging.getLogger('tcpsocket')
        self.s = socket()
        self.s.connect((host,port))
        self.fh = self.s.makefile(mode="rw", encoding="utf-8")
        log.info(f"Connected to TCP {host}:{port}")
    def write(self, sth):
        "Expects sth to be a string"
        self.s.sendall(sth.encode("ascii"))
    def readline(self):
        # instead also: self.s.recv(123)
        return self.fh.readline()
    
class serial:
    "Small wrapper for making the use of PySerial more handy (no need for extra import)"
    def __init__(self, port, baudrate, **passed_options):
        log = logging.getLogger('serial')
        try:
            from serial import Serial  # requires pyserial
        except ImportError:
            raise ImportError("Please install PySerial in order to use it.")
        # in the following, some arguments are added for debugging...
        self.s = Serial(port, baudrate, 
            timeout=0.2, # in seconds            
            **passed_options)
        log.info(f"Connected to serial port {port} with {baudrate} baud")
        
        # As this class is for the HyCon, you should reset when reconnecting since
        # the UART tends to hold old data.
        
        import time
        max_reset_attempts = 10
        for i in range(max_reset_attempts):
            log.info(f"Attempt {i}/{max_reset_attempts} to reset the controller/connection...")
            self.write("x")  # reset instruction
            time.sleep(1) # sleep one second to allow reset
            res = self.readline()
            if res == "RESET\n":
                break
        
    def write(self, sth):
        self.s.write(sth.encode("ascii"))
    def readline(self):
        return self.s.readline().decode("ascii")
            
