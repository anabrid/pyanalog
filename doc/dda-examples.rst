.. _dda-examples:

Example circuits for DDA
========================

We have a number of example circuits written in either

* traditional DDA language (can be run with any DDA compiler)
* pythonic DDA (requires the PyDDA code but can be translated
  also to traditional DDA files)
* Jupyter/IPython notebook files (i.e. pythonic DDA but within
  a rich-text document)
  
These files are located in the `examples/` directory and are there for
being explored by interested users. A couple of files are gone into detail
in the following.

Traditional DDA circuits
------------------------

:download:`chua.dda <../examples/traditional-dda-circuits/chua.dda>`
   A traditional DDA code, implementing the Chua attractor from
   chapter 6.15 from Bernds new book (ap2.pdf). We have both a scaled
   and unscaled version along with a plotting code available in this
   repository. For plotting, we also have capabilities to do a
   high-quality "phase space" histogram based on massive binary output of the
   C++ integrator.
   
:download:`double-pendulum.dda <../examples/traditional-dda-circuits/double-pendulum.dda>`
   Another traditional DDA code, implementing a planar coupled gravity pendulum
   in classical small-angle approximation and in a formulation with two
   angles as degrees of freedom. The example stems from section 6.25 in
   Bernds new book (ap2.pdf). Again, we have a small Python code for plotting
   the results.
   
Command line DDA usage
----------------------

.. toctree::
   :maxdepth: 1
   
   shell-example
   

Python DDA circuits
-------------------

:download:`N-body.py <../examples/python-dda-circuits/N-body.py>`
   is an example python file which generates traditional DDA code.
   It implements N-body physics with an inverse square law force
   (Coulomb/Newton like); the initial data show two particles in a two
   dimensional simulation domain on a circular orbit.

   The code is written having in mind to compare the old dda2c.pl and
   the novel PyDDA implementation, therefore it has no coupling to
   the PyDDA code. It is in general not recommended to write PyDDA
   code like that.

:download:`md_water_toy.py <../examples/python-dda-circuits/md_water_toy.py>`
   A minimal molecular dynamics water toy simulation, basically an
   application of the N-body paradigm. This is a good and running example of
   a prototypical PyDDA application in science. It requires ``numpy``
   because it compiles vector/matrix like quantities. It is also
   equipped with a plotting/visualization of the simulation after
   being run with a generated C++ code.

Jupyter/IPython Notebooks
-------------------------

The notebooks are embedded within this documentation.

.. toctree::
   :maxdepth: 1

   examples/chua.ipynb
   examples/Heat-Equation.ipynb
