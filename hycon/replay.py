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
A HyCon command stream interpreter.

Will spill out LISP-like commands which can be fed into the hycon
again. This allows for replaying, which is helpful for a number of 
special scenarios such as:

* Offline-validating a HyCon instruction stream
* Man-in-the-middle inspecting an HyCon instruction stream
* Validating the correctness of high-level HyCon instructions
  (such as emitted by the PyFPAA or autosetup codes)

The code basically implements a character-by-character tokenizer/parser.
It is built based on a simple mapping datastructure which assigns each
one-letter command the respective PyHyCon method name. Furthermore,
method arguments can be read and converted.

It would be nice to join HyCon.py and replay.py to a single file which
translates between the serial protocol and the OOP API calls. The transformation
is quite trivial, but now we have a lot of code doing nothing of 
bigger interest.

The ordering follows the AVR Ino code.
"""

import sys, io, functools
identity = lambda x:x

from .HyCon import HyCon


def delayed(static_method):
    """
    This is a decorator for a static method in a class. It will
    make the function body "delayed", i.e. when calling the function,
    a future/promise/delay/deferred element is returned.
    Some parameter bounding (closure) happens: The decorated arguments
    are evaluated early while the later execution expects only a single
    reader argument. Example to follow the logic:
    
    >>> f = lambda a,b,c,d: print(a,b,c,d)
    >>> g = delayed(f)
    >>> h = g(1,2,3)
    >>> h(4)
    4 1 2 3
    """
    @functools.wraps(static_method)
    def decorated(*w,**kw):
        def deferred(reader):
            return static_method(reader, *w, **kw)
        #deferred.__name__ = f"{static_method.__name__}({str(w)[1:-1]}{',' if kw else ''}{str(kw)[1:-1]})"
        return deferred
    return decorated

class consume:
    """
    Consume is an ugly namespace and not a class, actually.
    The basic idea of these (static!) functions is to be
    called delayedly with a function as it's argument which
    acts like the io.IOBase.read() function, i.e. advances
    an internal cursor (side effect) and returns *n* characters
    from the stream. Crude Example:
    
    >>> tokenizer = [consume.exact("test"), consume.decimals(3), consume.exact("foo"), consume.hex(2)]
    >>> test = io.StringIO("test123fooAA")
    >>> reader = test.read
    >>> [ token(reader) for token in tokenizer ]
    ['test', 123, 'foo', 170]
    """
    @delayed
    def exact(reader, text):
        proof = reader(len(text))
        if proof != text: raise ValueError(f"Expected '{text}' but got '{proof}'.")
        return text
    @delayed
    def number(reader, digits, base, multiply=1):
        """
        Reads a number with #digit digits in some base. Can perform a multiplication afterwards.
        
        >>> consume.number(8,16)(io.StringIO("deadbeef").read)
        3735928559
        >>> consume.number(2,10,multiply=2)(io.StringIO("42").read)
        84
        """
        text = reader(digits)
        if not text: raise ValueError(f"Encountered end of input but expected {digits} digits in base {base}")
        try: return int(text,base) * multiply
        except ValueError as e: raise ValueError(f"Could not cast '{text}' as a base-{base} number.")
    @delayed
    def decimals(reader, number_of_digits):
        return consume.number(number_of_digits, 10)(reader)
    @delayed
    def hex(reader, number_of_digits):
        return consume.number(number_of_digits, 16)(reader)
    @delayed
    def list(reader, split, end, digits, base):
        """
        Reads a list of numbers. Limitations:
        * Always expects end token to come
        * All numbers must have same number of digits (and same base)
        * Cannot handle empty list or and won't accept end-of-file before end token.
        
        Examples:
        
        >>> consume.list(split=",",digits=1,base=10,end=".")(io.StringIO("1,5,2,3,9.").read)
        [1, 5, 2, 3, 9]
        >>> consume.list(split=":",digits=2,base=16,end=";")(io.StringIO("5a:88:ff:ff;").read)
        [90, 136, 255, 255]
        """
        assert len(split) == len(end)
        retlst = []
        while True:
            retlst.append( consume.number(digits, base)(reader) )
            #print(f"List: {retlst}")
            sep = reader(len(split))
            #print(f"Sep: '{sep}'")
            if sep == end: break
            elif sep != split: raise ValueError(f"Unexpected character(s) or end of stream: '{sep}'")
        return retlst

not_implemented = lambda comment: ("NOT_IMPLEMENTED", comment)

mapping = {
    "a": "disable_ovl_halt",
    "A": "enable_ovl_halt",
    "b": "disable_ext_halt",
    "B": "enable_ext_halt",
    "c": ("set_op_time", consume.decimals(6)),
    "C": ("set_ic_time", consume.decimals(6)),
    "d": ("digital_output", consume.decimals(1), False),
    "D": ("digital_output", consume.decimals(1), True),
    "e": "repetitive_run",
    "E": "single_run",
    "F": "single_run_sync",
    "f": "read_ro_group",
    "G": ("set_ro_group", consume.list(split=";", digits=4, base=16, end=".")),
    "g": ("read_element_by_address", consume.hex(4)),
    "h": "halt",
    "i": "ic",
    "L": not_implemented("Locate a computing element"),
    "l": "get_data",
    "o": "op",
    "P": ("set_pt", consume.hex(4), consume.hex(2), consume.number(digits=4, base=10, multiply=1./HyCon.DPT_MAX_INT_VALUE)),
    "q": "read_dpts", # is not_implemented()
    "R": "read_digital",
    "s": "get_status",
    "S": "pot_set",
    "t": "get_op_time",
    "x": "reset",
    "X": ("set_xbar", consume.hex(4), consume.hex(HyCon.XBAR_CONFIG_BYTES*2)),
    "?": not_implemented("Prints help")
}

class HyConRequestReader:
    """
    Converts HyCon "configuration strings" to high level API calls.
    This can be seen as the inverse operation to calling the HyCon.
    
    Instances of this class act as iterator. It will consume the
    incoming stream character by character (or the whole string, if
    given as a string).
    
    Example:
    
    >>> instructions = 'C000100c015000P0200000204P0300030000G0362;0363;0220;0221;0222;0223.'
    >>> commands = list(HyConRequestReader(instructions))
    >>> for c in commands: print(c)
    ('set_ic_time', 100)
    ('set_op_time', 15000)
    ('set_pt', 512, 0, 0.19941348973607037)
    ('set_pt', 768, 3, 0.0)
    ('set_ro_group', [866, 867, 544, 545, 546, 547])
    >>> replayed = io.StringIO()
    >>> hc = HyCon(replayed, unidirectional=True)
    >>> replay(hc, commands)
    >>> replayed.getvalue() == instructions
    True
    """
    def __init__(self, stream_or_string, mapping=mapping):
        self.subject = io.StringIO(stream_or_string) if isinstance(stream_or_string, str) else stream_or_string
        self.shadow = io.StringIO()
        self.mapping = mapping
    
    def read(self, size=-1):
        ret = self.subject.read(size)
        self.shadow.write(ret)
        return ret
    
    def debugline(self):
        read_in = self.shadow.getvalue()
        return f"Encountered after having read {len(read_in)} characters '{read_in}'"
        
    def read_arguments(self, rhs):
        if isinstance(rhs, tuple):
            return tuple(map(self.read_arguments, rhs))
        if callable(rhs):
            res = rhs(self.read)
            return res
        return rhs

    def read_command(self):
        command = self.read(1)
        if not command:
            raise StopIteration # end of input
        if command not in self.mapping:
            raise ValueError(f"Command '{command}' not part of the valid HyCon command characters. {self.debugline()}")
        return self.read_arguments(self.mapping[command])

    # act as an iterator
    __iter__ = identity
    __next__ = read_command
    
def replay(hycon, commands):
    """
    Given commands a list of tuples, this will mostly act like operator.methodcaller
    on them. If no arguments are given, the tuple can be omitted.
    
    Basic example:
    
    >>> class WannaBeHyCon:
    ...     def toot(self,x): print("too(%s)ooot" % x)
    ...     def bar(self): print("this is bar")
    ...     def buz(self,a,b,c): print(f"a*b = {a*b} but what is {c}")
    >>> replay(WannaBeHyCon(), [ "bar", ("toot", "fuz"), ("buz", 1,2,3) ])
    this is bar
    too(fuz)ooot
    a*b = 2 but what is 3

    The command format is produced by the HyConRequestReader and thus can be fed
    into this replay function:
    
    >>> replay(HyCon(sys.stdout, unidirectional=True), HyConRequestReader("xiohaARt"))
    xiohaARt
    
    This works for almost any useful instruction stream.
    """
    for command in commands:
        if not isinstance(command, tuple): command = (command,)
        method,*args = command        # LISP-like unpacking (command, *args)
        getattr(hycon, method)(*args) # calling
