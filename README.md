# An approach to programmable analog computers

This repository is my work bench for small
"pioneering" scripts to gain experience and
create examples for digital extensions to the
Analog Paradigm Model-1 analog computer.

Contents in directories:

 * `Mathematica`: Notebooks for Wolfram
   Mathematica which demonstrate the pipeline from
   symbolic expressions (or simple ordinary differential
   equations) to analog computing circuits.
   This was the first thing I did beginning of
   Dec 2019.

* `pyFPAA`: A small Python3 code for compiling
  instructions for the AP/M-1 Hybrid Controller (HC),
  especially for the DPT (digital potentiometers),
  XBAR (crossbar switch) and the HC itself. The input
  is a quite extensive machine description together
  with a program (basically an analog circuit), both
  in a minimalistic HDL written in YAML. See the
  `README` file there for more details.

* `circuits`: A number of example input for the
  pyFPAA compiler.


All contents in this directory are released under the
GPL3 by SvenK, if not mentioned otherwise.