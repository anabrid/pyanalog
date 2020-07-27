.. _cas:

Computer Algebra Interfaces
===========================

DDA implements a few parts of computer algebra system (CAS), especially with it's :ref:`abstract-syntax-tree`.
Since we don't want to reinvent the wheel, we interface with common computer algebra systems.
There are at least two popular for the Python ecosystem available:

- `SymPy <https://www.sympy.org/>`_, bundled within the `SciPy <https://www.scipy.org/>`_ package,
  can be easily used as a library
- `Sagemath <https://www.sagemath.org/>`_, which is more of a monolithic software

So far, we had quick success with adopting SymPy:

SymPy
-----

.. automodule:: dda.sympy
   :members:
   
 
