.. _overview:

Overview of PyAnalog
====================

The big picture
---------------


.. code-block:: none

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


The particular python modules
-----------------------------

First and foremost, this documentation is an API documentation.
Therefore, it mostly covers the functions and classes exposed
by the following three python modules:

* :ref:`PyDDA <dda-intro>` is a tool for simple algebraic transformations of equations
  and circuits as well as their numerical simulation.
  DDA stands for *Digital Differential Analyzer*.
* :ref:`PyFPAA <fpaa>` is a tool for compiling an electrical circuit to a machine
  architecture. This especially programs digital potentiometers and
  cross bar switches and relies on a minimalistic hardware description
  language (HDL) written in YAML.
  FPAA stands for *Field Programmable Analog Array*.
* :ref:`PyHyCon <hycon>` is an interface to a Model-1 *Hybrid Controller* in order to
  run a program, steer the operation and gain output data.
  
You can read more about the goals of this software at the page
:ref:`dda-rationale`. 

.. note::

   Currently, the DDA code is by far the biggest part of the pyanalog package.
   The Hybrid Controller client is also usable. The FPAA part is working on its
   own and there are interfaces to the PyHyCon, however the interface between
   DDA and FPAA is basically nonexistent in the moment.
