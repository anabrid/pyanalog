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
A HyCon command stream interpreter.

Will spill out LISP-like commands which can be fed into the hycon
again. This allows for replaying.

Like the HyConAVR code, this works character by character.


"""

# All these modules are Python internals
import sys, re, logging, time
from collections import namedtuple
from copy import deepcopy

#logging.basicConfig(level=logging.INFO) # only for testing
log = logging.getLogger('HyCon') # or __name__

# Basis: AVR Ino code

# todo: HyCon.methodname instead of string

{
    "a": "disable_ovl_halt",
    "A": "enable_ovl_halt",
    "b": "disable_ext_halt",
    "B": "enable_ext_halt",
    "c": ("set_op_time", consume(decimals=6)),
    "C": ("set_ic_time", consume(decimals=6)),
    "d": ("digital_output", consume(decimals=1), False),
    "D": ("digital_output", consume(decimals=1), True),
    "e": "repetitive_run",
    "E": "single_run",
    "F": "single_run_sync",
    "f": "read_ro_group",
    "G": ("set_ro_group", consume(until=".", split=";", as="hex")), # or something similar...
    "g": ("read_element_by_address", consume(hexadecimals=4)),
    "h": "halt",
    "i": "ic",
    "L": not_implemented("Locate a computing element"),
    "l": "get_data",
    "o": "op",
    "P": ("set_pt", consume(hex=4), consume(hex=2), consume(decimals=4)),
    "q": "read_dpts", # is not_implemented()
    "R": "read_digital",
    "s": "get_status",
    "S": "pot_set",
    "t": "get_op_time",
    "x": "reset",
    "X": ("set_xbar", consume(hex=4), consume(hex=HyCon.XBAR_CONFIG_BYTES*2)),
    "?": not_implemented("Prints help")
}

# else/default: Illegal command.
