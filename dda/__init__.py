#
# Copyright (c) 2020 anabrid GmbH
# Contact: https://www.anabrid.com/licensing/
#
# This file is part of the DDA module of the PyAnalog toolkit.
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
PyDDA is a small library to write and generate DDA code in Python.
DDA stands for *digital differential analyzer*. In this context, it is
a code for solving ordinary differential equations given in a domain
specific language description (i.e. an electrical circuit).

The main advantage of this implementation in contrast to the older Perl
implementation is the *abstract syntax tree* level of circuit representation.
The syntax tree representation allows for fine-grained manipulations of
terms where the older Perl code could only apply regular expressions.

This code can replace the old ``dda2c.pl`` Perl implementation. It is a
standalone Python 3 code with no third party dependencies. It generates
standalone C++ code with no dependencies (not even on the old ``dda.h``).

Usage: As a library or from the command line
--------------------------------------------

This module can either be used from a DDA file written in Python or 
directly from old-style traditional DDA plaintext files. While pythonic
dda files have the advantage to be able to use all the flexibility of
Python scripting (such as using numpy for linear algebra computations
and matplotlib for postprocessing of results), plaintext DDA files are
in general shorter and more precise to read. See :mod:`dda.dsl` for further
details on the *traditional* DDA file format.

The module can also be used from the command line as a utility. The
behaviour is similar to the ``simulate.pl`` and ``dda2c.pl`` utilities but also
covers a few more features. Usage example:

::

    me@localhost $ python -m dda --help
    usage: dda.py [-h] [-o [OUTPUT]] [circuit_file] {c,dda,dot,latex}

    PyDDA, the AST-based DDA compiler

    positional arguments:
    circuit_file          DDA setup (traditional file). Default is stdin.
    {c,dda,dot,latex}     File formats which can be generated

    optional arguments:
    -h, --help            show this help message and exit
    -o [OUTPUT], --output [OUTPUT]
                            Where to write exported code to. Default is stdout.

    A Command Line Interface (CLI) for PyDDA...

See :meth:`dsl.cli()` for the implementation/further details.

Known Bugs and limitations
--------------------------

Please see the issue list at https://lab.analogparadigm.com/koeppel/dda/-/issues/
for a list of bugs.
""" 

import sys

assert sys.version_info >= (3, 6), \
   "PyDDA uses f-strings all the ways, which require Python 3.6."


def export(state, to, **kw):
    """
    Convenience function to export (transform) a state to some other
    programming language.

    Possible formats (allowed values for ``to``) supported so far are:
    
    * C/C++ (via :py:mod:`dda.cpp_exporter`)
    * DDA   (via :py:mod:`dda.dsl`)
    * SymPy (via :py:mod:`dda.sympy`)
    * Latex (via :py:mod:`dda.sympy`)

    This function shall be nice, so it accepts many spelling/notation
    of these language names.

    The return value are typically strings or tuples, dicts. There should
    be no side effects.
    """
    import re
    from .cpp_exporter import to_cpp
    from .dsl import to_traditional_dda
    from .sympy import to_sympy, to_latex
    exporters = {
        r"c(\+\+|pp)?": to_cpp,
        "dda": to_traditional_dda,
        "sympy": to_sympy,
        "latex": to_latex,
    }
    for k,v in exporters.items():
        if re.match(k, to, re.IGNORECASE):
            return v(state, **kw)
    raise ValueError(f"Export format {to} not known. Valid (regexps) are {list(exporters.keys())}.")

def clean(thing, target="C"):
    """
    Cleans an identifier for being compatible with the `target` language. This can be something like
    `C`, `python` or `dda` (cf. languages supported by :py:meth:`dda.export`) or also `latex`.
    
    It will basically try to transliterate all Unicode to ASCII and then try to ensure that the
    identifier is a valid C variable name (i.e. don't start with numbers, etc.).
    
    This function is nice, if you pass a :py:class:`dda.State` or :py:class:`dda.Symbol`, it will
    map the whole State/Symbol. Otherwise, it expects a string.
    
    Examples:
    
    >>> clean(r"\frac{x}{y}")
    'fracxy'
    >>> clean(r'a^{-1}')
    'a__1'
    >>> clean('a^b_c^{ef}')
    'a_b_c_ef'
    >>> clean(u'µ²')   # only if python package "unidecode" is installed # doctest: +SKIP
    'u2'
    >>> clean('77%alc')   # well, you can use numbers at the beginning of strings
    '_77alc'
    """
    import re, functools
    wants = lambda expr: re.match(expr, target, re.IGNORECASE)

    if isinstance(thing, State) or isinstance(thing, Symbol):
        return thing.map_heads(functools.partial(clean, target=target))
    elif not isinstance(thing, str):
        raise TypeError(f"Can only operate on strings (or States, Symbols, for convenience), but got '{thing}', which is of type {type(thing)}.")
    else:
        identifier = thing
        original = identifier # keep a copy

    # First, compose a decoder to remove any non-ascii stuff:
    try:
        from unidecode import unidecode
        identifier = unidecode(identifier)
    except ImportError as e:
        identifier = identifier.encode("ascii", errors="ignore").decode()

    if wants(r"c(\+\+|pp)?|python") or wants("dda"):
        if re.match(r"^\d", identifier):
            identifier = "_" + identifier

        identifier = identifier.replace("{","").replace("}","").replace("^","_").replace("\\","")

        # a^{-1} gets a_m1 and -a gets _a but a-b-c gets a_b_c
        identifer = re.sub(r"(\W)-", r"\1m", identifier)
        identifer = re.sub(r"^-", r"m", identifier)
        identifier = identifier.replace("-","_")

        # Remove anything left
        allowed = "_0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXY"
        identifier = "".join(c for c in identifier if c in allowed)
    elif wants("tex"):
        # Don't do anything, expect the user to be able to write valid latex identifiers.
        pass

    if not identifier: # empty string?
        raise ValueError(f"Identifier '{original}' is so weird that it was chopped to an empty string by the clean() function. Please choose a more subtle identifier.")

    return identifier

# populate namespace with some useful objects which should
# live in the package namespace.

from .ast import Symbol, State, BreveState, symbols, is_symbol
from .computing_elements import dda, dda_functions, dda_symbols
from .sympy import to_sympy
