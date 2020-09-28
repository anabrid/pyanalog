.. _dda-rationale:

A rationale about DDA
=====================

The following text is an introduction into the *DDA* concepts. It is envisaged for readers
who want to trace the connections between analog computing and it's digital simulation.
If you only want to work with `PyDDA` but do not care about the fundamentals, you can
skip this text.


The digital number flow machine
-------------------------------

DDA is short for *digital differential analyzer*. This term describes a certain way of
building an algorithmic-logical unit which is programmed with a dataflow paradigm. It
can be imagined as an analog computer but with digital computing elements in place of
analog computing elements. Such a DDA machine could feature *n* bit integer adders
(for instance a ripple-carry adder), binary multipliers, and even discrete integrators
for adding integers (i.e. a stateful computing element). In general, it is straightforward
to design such a machine for some fixed width binary number representation. It is worth
emphasizing that such a machine neither features continous time nor continous number
representation as a real analog computer would have. Nevertheless, it is an interesting
computing architecture as it is half-way between an analog and a digital computer.

In the age of FPGAs (field programmable gate arrays), it is straightforward to generate
digital computing circuits by software descriptions. Furthermore, being a digital
computer, the DDA architecture can be simulated by any Turing machine. This makes it
straightforward to write a simulator for contemporary register machines (that is,
regular and widespread computers/processors).

Describing and simulating a DDA machine
---------------------------------------

The DDA code proposed in this document consists of several parts:

* An easy description language for the computational network (circuit)
* A compiler from that language to an iterative imperative code (Perl/C)
* Tools for running such a code and evaluating the results

Loosely speaking, this translation works as follows: A circuit file is an ASCII
line based text file which looks like

.. code-block:: python

    dt = const(0.0005)
    t = int(1, dt)
    y0  = const(-1)
    minus_dy0 = const(-1)

    minus_dy = int(y, dt, minus_dy0)
    y        = int(minus_dy, dt, y0)
    
That is, each line is an assignment of some variable to some expression, which is either
a constant (``const``) or a compound expression of computing elements. These expressions
are written in some standard C-like notation ``f(x,y,...)`` where ``f`` is the identifier for
the function and ``x,y,...`` are comma seperated arguments. The following *basic arithmetic*
(from the perspective of an analog computer) computing elements are defined:

* :math:`neg(x) = -x`, the inverse
* :math:`div(x, b) = a/b`, the standard division
* :math:`mult(a_0, a_1, \dots) = \prod_i a_i`, the standard multiplication
* :math:`sum(a_0, a_1, \dots) = - \sum_i a_i`, the summation in analog-computer typical
  *negating* convention.
* :math:`int(a_0, a_1, \dots, \Delta t, I_0) \approx - \int \sum_i a_i \, \Delta t + I_0`,
  the time integration (again in analog-computer typical negating convention).
  The digital integrator is discussed in detail in the following text.

Furthermore, a couple of case-discreminating computing elements are defined. Here,
they are given in C-like notation ``x ? y : z`` which evaluates to ``if(x) then y else z``.

* ``lt(a,b,c,d) = (a <  b) ? c : d``
* ``le(a,b,c,d) = (a <= b) ? c : d``
* ``gt(a,b,c,d) = lt(b,a,c,d)``
* ``ge(a,b,c,d) = le(b,a,c,d)``
* ``dead_lower(a,b) = (a<b) ? (a-b) : 0 = gt(a,b,a-b,0)``
* ``dead_upper(a,b) = (a>b) ? (a-b) : 0 = lt(b,a,a-b,0) ``
* ``min(a,b) = (a<b) ? a : b = lt(a,b,a,b)``
* ``max(a,b) = (a>b) ? a : b = gt(a,b,a,b)``
* ``abs(a) = (a<0) ? -a : a  = lt(a,0,-a,a)``
* ``floor(a) = (int)a``  rounds ``a`` to the next lower integer.

Linearization of a circuit
--------------------------

The ``dda2c.pl`` Perl script translates a DDA circuit file to a valid *C* program. To do
so, all quantities are treated as *real valued* and are associated with the *double*
floating point data type. As C is a strongly typed language, all defined quantities are
collected and introduced as stack variables before use.

The actual imperative program then just takes the DDA circuit line-by-line. This introduces
a bias, as the computing network by itself is executed *synchronously* while a simulation
with a single arithmetic logical unit (ALU) on an ordinary processor can only execute one
operation at a time.

.. note::

   It would be interesting to think a bit whether we could not write an DDA-level exact
   simulator, since the DDA machine is clocked. We should be able to correctly simulate
   this clock.

Since the DDA is subject to a discrete computing cycle, a register machine can simulate
the DDA architecture cycle by cycle, computing the value of each computing element
input and output. For the sake of extraordinary introspection and debugging facilities,
the DDA to C compiler dismantles compound expressions ``f(g(x))`` or ``f(a,b(c),d(e))``
and entitles all intermediate expressions such as ``gx=g(x)`` in ``f(gx)`` or
``g=b(c)`` and ``h=d(e)`` in ``f(a,g,h)``. This is especially handy when the DDA is seen
as an approximation of the analog computer, as it allows for checking the boundness
(correct scaling) of all variables during the cycles (time evolution).

Having said that, the DDA simulator allows for simulating a DDA circuit iteration by
iteration and dumping (outputting) values every *n*th iteration. Therefore, while
the input of a circuit is always fixed by the constants (``const`` statements, no
focus has given to the point of interfacing other codes, which is left as an exercise
for the reader), the output is always a time series for a given set of quantities. We
refer to theses quantities as *observables*, which are *queried* for at code generation
time. One can thus understand the output as a fully discrete table of numbers, where
the columns hold the time series for a given variable and the each row stands for one
time iteration (or some average or surrogate for a larger number of iterations, if
requested). These numbers are represented as ASCII column seperated values (CSV) in the
output of the compiled C program.

Applicability for solving differential equations
------------------------------------------------

The usability for this software-based DDA implemenetation for solving ordinary differential
equations highly depends on the internals of the integrator component. From all computing
elements described above, the integrator is the only one with an *internal state*. That
is, it has to remember from iteration to iteration the current integration value.

The most easy integrator component will internally look like the following imperative
dummy code:

.. code-block:: c

    double integrate(double integrand, double dx, double initial_value) {
        static double internal_state = initial_value;
        internal_state += integrand * dx;
        return internal_state;
    }

Here, the ``internal_state`` is declared as a *static* variable, which you can think of a
global variable (with a lifetime longer then the function evaluation) if you don't know C.
In fact, this dummy code comes quite close to the actual implementation of the integrator
in the DDA C code. We refer to the above numerical scheme as the *Euler time integration*,
since it approximates the time-continous integral by it's Riemann sum.

Within the DDA code, higher order explicit integration schemes can be chosen, such as
Runge-Kutta. However, given the nature of the problem description in a circuit, implicit
methods can not be applied by the compiler without an actual analysis of the differential
equation. Howver, on can imagine a DDA circuit which itself describes a numerical scheme
on a digital-circuit level.   
   
   
On PyDDA, the scucessor of the DDA Perl code
--------------------------------------------
The first DDA code was written by Bernd. It's job was to simulate circuits, and this was
performed by a small Perl script which threw a few regexes onto the DDA file to convert it
to an executable C numeric simulation.

As described above, we found out that even with slightly more challenging circuits (kind of *border
cases*, such as the depicted one above) the simple ideology of looping over numeric
equations breaks down.

Lexical sorting of variable dependencies
----------------------------------------

Instead, was has to be applied for a stable integration of an electric circuit, i.e. an
ordinary differential equaiton, is the correct sorting of equation ordering. To do so,
we must study the dependencies of equations. This requires a memory representation of
equations, and there we enter the domain of *computer algebra systems* (CAS). Their central
piece of information are algebraic equations, which are typically represented as
(abstract) *syntax trees*.

PyDDA was an effort to rewrite the Perl-based DDA with a minimal amount of work.
Exploiting that DDA looks almost like Python, the idea was to bring a number of 
archivements with a single code:

- Allow to write high-level DDA codes, which probably involve indexing, n-dimensional
  arrays, etc.
- Allow for easy interoperation with various codes and tools, such as other CAS,
  (evventually generated) numerical simulation codes  or reprogrammable analog computers.
- Enable the user for a Read-eval-print loop interface (REPL) in order to encourage
  explorative programming.
- Meshing literate programming, generation of documentation and reports out of the
  equations without much work
- Picking the community where it is: Scientific Python is a thing, and so we choose
  python. Thus we also can stick to python when it comes to simulation analysis and
  postprocessing.
- Avoid dependencies if not neccessary. Don't reinvent the wheel, but try out how
  far we can get without employing a large computer algebra system.

