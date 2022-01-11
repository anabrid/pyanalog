.. _fpaa:

About FPAA
==========

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

.. automodule:: fpaa
   :members:

.. automodule:: fpaa.fpaa
   :members:

