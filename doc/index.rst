Pyanalog: A pythonic analog computer demonstrator interface
===========================================================

.. raw:: latex

   \section*{Abstract and Summary of PyAnalog}


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



.. raw:: latex

   \chapter{Introduction}

.. toctree::
   :maxdepth: 2
   :caption: Introduction

   overview
   installation
   tips
   code-testing
   
.. raw:: latex

   \chapter{PyDDA}
   
.. toctree::
   :maxdepth: 2
   :caption: PyDDA

   dda/intro
   dda/rationale
   dda/api-reference
   dda/examples
   
.. raw:: latex

   \chapter{PyFPAA}
   
.. toctree::
   :maxdepth: 2
   :caption: FPAA
   
   fpaa/fpaa
   fpaa/examples
   fpaa/mini-m1
   
.. raw:: latex

   \chapter{PyHyCon}
   
.. toctree::
   :maxdepth: 2
   :caption: Hybrid Controller
   
   hycon/hycon
   hycon/networking
   
.. raw:: latex

   \appendix
   \chapter{Appendix} % or: Endnotes

About this documentation
------------------------

This documentation is written in `ReStructured text <https://en.wikipedia.org/wiki/ReStructuredText>`_ 
(RST) and rendered using the `Sphinx <https://www.sphinx-doc.org/>`_. documentation
system. Possible output formats are not only web pages (HTML), but also PDF,
amongst others. If you have sphinx installed (``pip install sphinx``), you can
just go to the ``doc`` directory and type ``make html`` or ``make pdf`` to
generate the docs locally. If you have a mixed Python2/Python3 system, call
``make html SPHINXBUILD="python3 -msphinx"`` to ensure using Python3.

If you want to start editing/improving this documentation, you might want to
read the `ReStructuredText Primer <https://docutils.sourceforge.io/docs/user/rst/quickstart.html>`_. A handy tool for hot reloading (regenerating) the documentation
during editing is `Sphinx-Reload <https://github.com/prkumar/sphinx-reload>`_. After
installation, just run ``sphinx-reload doc/`` from the root directory and point your
browser to an address such as http://localhost:5500/.

This documentation is automatically updated/built at Git commit/push time by our
Gitlab Continous Integration infrastructured and uploaded
as static files to our `Anabrid Dev Server <https://www.anabrid.dev/>`_
(formally `Read The Docs <https://readthedocs.org/>`_). you can find the docs at:

- https://anabrid.dev/pyanalog/dirhtml/ primary link
- https://anabrid.dev/pyanalog/latex/pyanalog.pdf for a +100 page
  printable/downloadable/searchable PDF version
- Various different versions for download at https://anabrid.dev/pyanalog/


Indices and tables
------------------

* :ref:`Python Function/Class index <genindex>`
* :ref:`Python module index <modindex>`

..
   Linking to search makes no sense since the search box
   is omnipresent in the RTD theme
   * :ref:`search`
