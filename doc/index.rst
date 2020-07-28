Pyanalog: A pythonic analog computer demonstrator interface
===========================================================

`pyanalog` is a `Python3 <https://www.python.org/>`_ package and 
demonstrator code for a software stack for analog computers developers.
It can

* manipulate ordinary differential equations in a way suitable for
  procession with the exemplary *Model-1 Analog Computer*
* simulate circuits and generate C++ code for them
* generate and manipulate netlists and VHDL-like circuit descriptions
* compile against machine architectures on a macrocell-level,
  set digital potentiometer arrays, cross bar switches, digital switches,
  etc.
* interface a Model-1 hybrid controller in order to run a program,
  steer the operation and gain output data.
  
The codes are supposed to work well in the
[Scientific Python](https://www.scipy.org/) ecosystem. The target 
audience are clearly software engineers and scientists. The user
interface is either command line (bash or python shell) or scripting
(python or C/YAML-like domain specific languages). This code can
interface with remote analog computers (AAAS - analog computing
as a service).

The `pyanalog` code is open-source,  *currently work in progress* and
authored by the upcoming `Anabrid Inc. <http://anabrid.com>`_. 

The particular python modules
-----------------------------

First and foremost, this documentation is an API documentation.
Therefore, it mostly covers the functions and classes exposed
by the following three python modules:

* `PyDDA` is a tool for simple algebraic transformations of equations
  and circuits as well as their numerical simulation.
  DDA stands for *Digital Differential Analyzer*.
* `PyFPAA` is a tool for compiling an electrical circuit to a machine
  architecture. This especially programs digital potentiometers and
  cross bar switches and relies on a minimalistic hardware description
  language (HDL) written in YAML.
  FPAA stands for *Field Programmable Analog Array*.
* `PyHyCon` is an interface to a Model-1 *Hybrid Controller* in order to
  run a program, steer the operation and gain output data.
  
You can read more about the goals of this software at the page
:ref:`rationale`. 

Contents
--------

.. toctree::
   :maxdepth: 1
   :caption: Introduction

   installation
   tips
   code-testing


.. toctree::
   :maxdepth: 1
   :caption: PyDDA

   rationale
   intro
   ast
   dsl
   computing_elements
   cas
   
.. toctree::
   :maxdepth: 1
   :caption: FPAA
   
   fpaa
   
.. toctree::
   :maxdepth: 1
   :caption: Hybrid Controller
   
   hycon
   

About this documentation
------------------------

This documentation is written in `ReStructured text <https://en.wikipedia.org/wiki/ReStructuredText>`_ 
(RST) and rendered using the `Sphinx <https://www.sphinx-doc.org/>`_. documentation
system. Possible output formats are not only web pages (HTML), but also PDF,
amongst others. If you have sphinx installed (``pip install sphinx``), you can
just go to the ``doc`` directory and type ``make html`` or ``make pdf`` to
generate the docs locally. If you have a mixed Python2/Python3 system, call
``make html SPHINXBUILD="python3 -msphinx"`` to ensure using Python3.

Since the code is currently developed in a private repository, we do not yet make
use of services such as `ReadTheDocs <http://readthedocs.io/>`_ but generate and
upload the documentation on code change to a private website using Gitlab-CI.
You find these automatically built files at:

- http://ai.svenk.org/html/ for HTML pages
- http://ai.svenk.org/dirhtml/ for HTML pages with nicer links
- http://ai.svenk.org/text/ for text files ;-)
- http://ai.svenk.org/latex/pydda.pdf for a PDF version


Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
