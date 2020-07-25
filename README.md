# A pythonic analog computer demonstrator interface

This repository holds three libraries which should allow to interface
analog computers on a software developer/mathematican level:

* `PyDDA` is a tool for simple algebraic transformations of equations
  and circuits as well as their numerical simulation.
* `PyFPAA` is a tool for compiling an electrical circuit to a machine
  architecture. This especially programs digital potentiometers and
  cross bar switches and relies on a minimalistic hardware description
  language (HDL) written in YAML.
* `PyHyCon` is an interface to a Model-1 Hybrid Controller in order to
  run a program, steer the operation and gain output data.
  
## Big picture

```
Input: Ordinary Differential Equation in mathematical notation
       (for instance in SymPy, Sage, Matlab, Latex, etc.)
     |
     v
     
PyDDA: Generation of a circuit
     |
  +--+---+   Several backends to deal with the
  |  |   |   circuits, for instance:
  | ...  |
  |      +--> Simulation with numerics (C++ or SciPy/Netlib ODE solver)
  |
  v

PyFPAA:  Circuit synthesis (=mapping) with based on architecture
         description.
  |
  |
  v

PyHyCon: Interaction with Analog-as-a-service
         (SSH to the small analog machine in Bernds basement)
  |
  v
  
Output: Measurement data from all relevant fields
```
  
## DDA and Analog synthesis codes

The particular directories hold several codes:

* PyDDA is a Python3 package for analog circuit simulation
* DDA is a Perl5 code for analog circuit simulation

There should also be examples, somewhere.

The overall plan is to open source these codes or parts of them end of 2020.

## PyFPAA: An approach to programmable analog computers

See the readme below ``PyFPAA``.

## PyHyCon: A Python Hybrid Controller interface

A clone of the Perl `IO::HyCon` library. See the code for
further details.
