# The PyFPAA compiler

This directory contains a small compiler prototype for programmable analog
computers (FPAAs). As machines, we have so far the minimal setup for the
*Analog Paradigm Machine-1* which can be found in `AP-M1-Mini.yml`.

## Features

* YAML files instead of VHDL (or some AHDL) for rapid prototyping
* Description of primitive as well as high-level analog computing parts
  (for instance both a simple summer as well as a summer with
  a subsequent inverter are possible.
* Program description can be quite expressive: Programming parts can
  be given custom labels, variables can be used for coefficients,
  and much more

## Shortcomings

* We don't use a standarized HDL yet
* We don't yet model the internals of high-level computing parts yet,
  so the wiring instructions/descriptions lack a full modeling of the
  target machine.
