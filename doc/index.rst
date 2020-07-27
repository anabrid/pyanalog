PyDDA documentation
===================

**PyDDA** is a `Python3 <https://www.python.org/>`_ package for generating and
manipulating analog computer circuits. DDA stands for *Digital Differential
Analyzer*. PyDDA is open-source, *currently work in progress* and authored by
`Anadigm Inc. <http://anadigm.com>`_. 
You can read more about the goals of this software at the page
:ref:`rationale`. Furthermore, this documentation covers the API exposed by
PyDDA. 

Contents
--------

.. toctree::
   :maxdepth: 1
   :caption: Introduction

   installation
   rationale
   intro

.. toctree::
   :maxdepth: 1
   :caption: API

   ast
   dsl
   computing_elements
   cas

      
.. toctree::
   :maxdepth: 1
   :caption: Development

   tips
   code-testing
   

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
- PDF: todo


Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
