"""
PyFPAA is a compiler for programmable analog computers (FPAAs). It was written by SvenK in Dec 2019
for quickly approaching a testing infrastructure for the XBAR module for the *Analog Paradigm M-1*
analog computer.

The script requires a (lengthy) machine description, which encodes the computational parts
available and is quite similar to a machine library in VHDL. That file encodes especially the
hard-wired vs. configurable parts of the machine.
The actual program is then rather short and describes how the configurable computational parts
are connected with each other. It also specifies constant coefficients which are set with
digital potentiometers or other digital steering parameters.

The output of the code is the analog computer configuration, as required by PyHyCon. This can
be either

* a single line of text, which are mostly hexadecimal encoded
  instructions together with command characters, all following the serial console protocol which
  the HybridController of the machine expects (http://analogparadigm.com/downloads/hc_handbook.pdf).
* configuration tuples for PyHyCon
* or a direct API to PyHyCon

In order to run this program, all you need is PyYAML to read the YAML files. If you want
to draw circuit plots, you need matplotlib.
"""

# Populate namespace

from .fpaa import load_from_yaml, synthesize, compile_instructions
