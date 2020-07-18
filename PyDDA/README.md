Welcome to the PyDDA package
============================

This directory holds the package root directory (where setup.py lives)
of the PyDDA package. This is mostly a pure Python3 package with no
dependencies.

If you are lazy, you can start using PyDDA right from here:

$ git clone git@lab.analogparadigm.com:koeppel/dda.git
$ cd dda/PyDDA
$ python3
>>> from pydda import *
>>> s = BreveState()
>>> s.x = Symbol("int", "x", 0.02, 0)
>>> print(s)
State({'x': int(x, 0.02, 0)})

Please inspect the doc/ directory for instructions how to use the
package. It contains also instructions how to install PyDDA properly.
Try to run "make" therein to see the various formats you can read
the documentation in.

Keep analog!

