.. _dda-intro:

Introduction to PyDDA
=====================

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

The ``dda`` module can either be used from a DDA file written in Python or 
directly from old-style traditional DDA plaintext files. While pythonic
dda files have the advantage to be able to use all the flexibility of
Python scripting (such as using numpy for linear algebra computations
and matplotlib for postprocessing of results), plaintext DDA files are
in general shorter and more precise to read. See :mod:`dda.dsl` for further
details on the *traditional* DDA file format.

The module can also be used from the command line as a utility. The
behaviour is similar to the ``simulate.pl`` and ``dda2c.pl`` utilities but also
covers a few more features. Usage example (implementation
provided by :meth:`dsl.cli()` ):

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

Here is a full bash script which demonstrates how to use PyDDA as a drop-in replacement
for the traditional Perl-based DDA code. It allows using the PyDDA C++ code generator
without writing a single line of Python:

::

    #!/usr/bin/bash
    
    # given the DDA file "notch_simplified.dda", we simulate the system
    # for 2000 timesteps and plot the time evolution of the fields "cn", "cd" and "cnr"
    # which are part of the DDA file (in terms of "cn = int(...)")

    python -m dda notch_simplified.dda C --output notch_simplified.cc
    g++ --std=c++17  notch_simplified.cc -onotch_simplified.exe

    ./notch_simplified.exe --max_iterations=2000 --skip_header=1  cn cd cnr  > scratch.dat

    cat <<GNUPLOT_FILE > gnuplot.dat

    set terminal pdf
    set output "notch_simplified_gnuplot.pdf"
    set key autotitle columnheader
    set title "Notch simplified (with PyDDA/Gnuplot)"

    plot "scratch.dat" using 1 with lines title "cn", \
         "scratch.dat" using 2 with lines title "cd", \
         "scratch.dat" using 3 with lines title "cnr"

    GNUPLOT_FILE

    gnuplot gnuplot.dat
    open notch_simplified_gnuplot.pdf



Known Bugs and limitations
--------------------------

Please see the issue list at https://github.com/anabrid/pyanalog/issues for
a list of bugs.

We also have an internal bug tracker at
https://lab.analogparadigm.com/software/pyanalog/-/issues
which is subject to be merged into the public one.
