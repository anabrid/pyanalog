.. _cas:

Computer Algebra Interfaces
---------------------------

DDA implements a few parts of computer algebra system (CAS), especially with it's :ref:`abstract-syntax-tree`.
Since we don't want to reinvent the wheel, we interface with common computer algebra systems.
There are at least two popular for the Python ecosystem available:

- `SymPy <https://www.sympy.org/>`_, bundled within the `SciPy <https://www.scipy.org/>`_ package,
  can be easily used as a pure python library.
- `Sagemath <https://www.sagemath.org/>`_, which is more of a monolithic software.
  The symbolic foundation of sage is provided by `Ginac <https://ginac.de/>`_ and
  `Pynac <http://pynac.org/>`_, respectively. Many open source computer algebra systems are bundled
  with sage, such as `Maxima <http://maxima.sourceforge.net/>`_ and
  `Octave <https://www.gnu.org/software/octave/>`_. Furthermore, interfaces to many others such as
  `Maple <https://maplesoft.com/>`_, `Mupad <https://www.mathworks.com/discovery/mupad.html>`_ or
  `Mathematica <https://www.wolfram.com/mathematica/>`_ are part of sage.

So far, we had quick success with adopting SymPy (see next section).

SymPy module API reference
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: dda.sympy
   :members:
   
 
