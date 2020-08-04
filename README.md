# Pyanalog: A pythonic analog computer demonstrator interface

This repository holds a python package called `pyanalog`.
It consists three libraries which should allow to interface
analog computers on a software developer/mathematican level:

* `PyDDA` is a tool for simple algebraic transformations of equations
  and circuits as well as their numerical simulation.
* `PyFPAA` is a tool for compiling an electrical circuit to a machine
  architecture. This especially programs digital potentiometers and
  cross bar switches and relies on a minimalistic hardware description
  language (HDL) written in YAML.
* `PyHyCon` is an interface to a Model-1 Hybrid Controller in order to
  run a program, steer the operation and gain output data.
  
## Please see the docs!
See doc/index.rst or call "make docs".
You can also go to http://ai.svenk.org/html/ for the rendered docs.
  
## DDA and Analog synthesis codes

The particular directories hold several codes:

* PyDDA is a Python3 package for analog circuit simulation
* DDA is a Perl5 code for analog circuit simulation

There should also be examples, somewhere.

The overall plan is to open source these codes or parts of them end of 2020.

## PyFPAA: An approach to programmable analog computers

PyFPAA is a work bench for small
"pioneering" scripts to gain experience and
create examples for digital extensions to the
Analog Paradigm Model-1 analog computer.

`pyFPAA` is a small Python3 code for compiling
instructions for the AP/M-1 Hybrid Controller (HC),
especially for the DPT (digital potentiometers),
XBAR (crossbar switch) and the HC itself. The input
is a quite extensive machine description together
with a program (basically an analog circuit), both
in a minimalistic HDL written in YAML. See the
`README` file there as well as the `doc` directory 
for more details.

See also `examples/fpaa-circuits` for a number of example
input for the pyFPAA compiler. There also exist basic
test scripts within `tests`.

Within `misc` , there are old files:

 * `Mathematica`: Notebooks for Wolfram
   Mathematica which demonstrate the pipeline from
   symbolic expressions (or simple ordinary differential
   equations) to analog computing circuits.
   This was the first thing I did beginning of
   Dec 2019.

## PyHyCon: A Python Hybrid Controller interface

A clone of the Perl `IO::HyCon` library. See the code for
further details.


# How to use

This directory holds the package root directory (where setup.py lives)
of the PyDDA package. This is mostly a pure Python3 package with no
dependencies.

If you are lazy, you can start using PyDDA right from here:

```
$ git clone git@lab.analogparadigm.com:koeppel/dda.git
$ cd dda/PyDDA
$ python3
>>> from pydda import *
>>> s = BreveState()
>>> s.x = Symbol("int", "x", 0.02, 0)
>>> print(s)
State({'x': int(x, 0.02, 0)})
```

Please inspect the doc/ directory for instructions how to use the
package. It contains also instructions how to install PyDDA properly.
Try to run "make" therein to see the various formats you can read
the documentation in.

Keep analog!

