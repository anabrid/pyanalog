# Pyanalog: A pythonic analog computer demonstrator interface

This repository holds a python package called `pyanalog`.
It consists of three libraries which allow to interface
analog computers on a software developer/mathematican level:

* `PyDDA` is a tool for simple algebraic transformations of equations
  and circuits as well as their numerical simulation.
* `PyFPAA` is a tool for compiling an electrical circuit into a machine
  architecture. This especially sets digital potentiometers and
  cross bar switches and relies on a minimalistic hardware description
  language (HDL) written in YAML.
* `PyHyCon` is an interface to a Model-1 Hybrid Controller in order to
  run a program, steer the operation and gain output data.
  
## Please see the docs!
See doc/index.rst or call "make docs".
You also find the generated docs at https://www.anabrid.dev/pyanalog/

We used to serve them from https://pyanalog.readthedocs.io/ but this
page is known to be faulty.
  
## PyFPAA: An approach to programmable analog computers

PyFPAA is a work bench to gain experience with hybrid computer programming.
It can be used to create examples for the digital/hybrid extensions of the 
Analog Paradigm Model-1 analog computer (AP/M-1).

`pyFPAA` is a small Python3 code for compiling
instructions for the AP/M-1 Hybrid Controller (HC),
especially for the DPT (digital potentiometers),
XBAR (crossbar switch) and the HC itself. The input
is a quite extensive machine description together
with a program (basically an analog circuit), both
written in a minimalistic HDL in YAML representation. See the
`README` file there as well as the `doc` directory 
for more details.

See also `examples/fpaa-circuits` for a number of example
input for the pyFPAA compiler. There also exist basic
test scripts within `tests`.

The `misc` directory also contains a number of old files:

 * `Mathematica`: Notebooks for Wolfram
   Mathematica which demonstrate the overall processing from
   symbolic expressions (or simple ordinary differential
   equations) to analog computer setups. (This was the first 
   thing I did starting in Dec 2019.)

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

Please have a look at the doc/ directory for instructions on how to use the
package. It contains also instructions how to install PyDDA properly.
Run "make" to see the various formats the documentation can be generated in.

Stay analog!

