Pyanalog: A pythonic analog computer demonstrator interface
===========================================================

``pyanalog`` is a `Python3 <https://www.python.org/>`_ package and 
demonstrator/research code for a software stack for analog computers.
It empowers users to

* manipulate ordinary differential equations in a way suitable for
  procession with the exemplary
  `Analog Paradigm Model-1 <http://analogparadigm.com/>`_
  analog computer or similar *high-level* architectures in terms of
  OpAmp-Level circuit description (*not* SPICE-level circuit description).
* simulate abstract computing circuits made of elements such as
  *summers, integrators, differentiator and multipliers*. The heart of the code is
  a :ref:`custom ODE solver (based on C++ codegeneration) <cpp-codegen>`,
  but also interfaces to :ref:`SciPy <dda-scipy>` and :ref:`SymPy <cas>`
  solvers exist. Notably, the C++ solver can also solve integro-differential
  equations.
* generate and manipulate
  :ref:`netlists and VHDL-like circuit descriptions <fpaa>`
* compile against machine architectures on a macrocell-level,
  set digital potentiometer arrays, cross bar switches, digital switches,
  etc.
* :ref:`interface a Model-1 hybrid controller <hycon>` in order to run
  a program, steer the operation, gain and visualize/postprocess output data.
  
The codes are supposed to work well in the
`Scientific Python <https://www.scipy.org/>`_ ecosystem. The target 
audience are clearly software engineers and scientists. The user
interface is either command line (bash or python shell) or scripting
(Python or C/YAML-like domain specific languages). This code can
interface with remote analog computers (AAAS – *analog computing
as a service*).

The ``pyanalog`` code is open-source and a *research code which is worked
actively on*, ie. it is "work in progress". It is authored 
`Anabrid GmbH <http://www.anabrid.com>`_. The code is currently
dual-licensed by `GPL-3 <https://github.com/anabrid/pyanalog/blob/master/LICENSE.GPL3>`_
and `a proprietary/commercial use license <https://github.com/anabrid/pyanalog/blob/master/LICENSE.ANABRID>`_.
See http://www.anabrid.com/licensing for further details.


Contents
--------

.. toctree::
   :maxdepth: 1
   :caption: Introduction

   overview
   installation
   tips
   code-testing


.. toctree::
   :maxdepth: 2
   :caption: PyDDA

   dda-intro
   dda-rationale
   dda-api-reference
   dda-examples
   
.. toctree::
   :maxdepth: 1
   :caption: FPAA
   
   fpaa
   fpaa-examples
   
.. toctree::
   :maxdepth: 1
   :caption: Hybrid Controller
   
   hycon
   hycon-networking
   
   

About this documentation
------------------------

This documentation is written in `ReStructured text <https://en.wikipedia.org/wiki/ReStructuredText>`_ 
(RST) and rendered using the `Sphinx <https://www.sphinx-doc.org/>`_. documentation
system. Possible output formats are not only web pages (HTML), but also PDF,
amongst others. If you have sphinx installed (``pip install sphinx``), you can
just go to the ``doc`` directory and type ``make html`` or ``make pdf`` to
generate the docs locally. If you have a mixed Python2/Python3 system, call
``make html SPHINXBUILD="python3 -msphinx"`` to ensure using Python3.

This documentation is both hosted at  `ReadTheDocs <http://readthedocs.io/>`_
as well as an `Anabrid Dev Server <https://www.anabrid.dev/>`_.  You can find
the docs at

- https://pyanalog.readthedocs.io/en/latest/
- https://www.anabrid.dev/dirhtml/ a mirror
- https://www.anabrid.dev/text/ for text files ;-)
- https://www.anabrid.dev/latex/pydda.pdf for a PDF version


Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
