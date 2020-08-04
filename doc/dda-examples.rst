.. _dda-examples:

Example circuits for DDA
========================

We have a number of example circuits written in traditional or pythonic DDA
in the `examples/` directory. These are for instance:

``N-body.py``
   is an example python file which generates traditional DDA code.
   It implements N-body physics with an inverse square law force
   (Coulomb/Newton like); the initial data show two particles in a two
   dimensional simulation domain on a circular orbit.

   The code is written having in mind to compare the old dda2c.pl and
   the novel PyDDA implementation, therefore it has no coupling to
   the PyDDA code. It is in general not recommended to write PyDDA
   code like that.

``md_water_toy.py``
   A minimal molecular dynamics water toy simulation, basically an
   application of the N-body paradigm. This is a good and running example of
   a prototypical PyDDA application in science. It requires ``numpy``
   because it compiles vector/matrix like quantities. It is also
   equipped with a plotting/visualization of the simulation after
   being run with a generated C++ code.

``chua.dda``
   A traditional DDA code, implementing the Chua attractor from
   chapter 6.15 from Bernds new book (ap2.pdf). We have both a scaled
   and unscaled version along with a plotting code available in this
   repository. For plotting, we also have capabilities to do a
   high-quality "phase space" histogram based on massive binary output of the
   C++ integrator.
   
``double-pendulum.dda``
   Another traditional DDA code, implementing a planar coupled gravity pendulum
   in classical small-angle approximation and in a formulation with two
   angles as degrees of freedom. The example stems from section 6.25 in
   Bernds new book (ap2.pdf). Again, we have a small Python code for plotting
   the results.
