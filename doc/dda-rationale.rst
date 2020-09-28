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
analog computing elements. Such a DDA machine could feature $n$ bit integer adders
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

* $$neg(x) = -x$$, the inverse
* $$div(x, b) = a/b$$, the standard division
* $$mult(a_0, a_1, \dots) = \prod_i a_i$$, the standard multiplication
* $$sum(a_0, a_1, \dots) = - \sum_i a_i$$, the summation in analog-computer typical
  *negating* convention.
* $$int(a_0, a_1, \dots, \Delta t, I_0) \approx - \int \sum_i a_i \, \Delta t + I_0$$,
  the time integration (again in analog-computer typical negating convention)

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
   
   
   
other stuff, to be joined
-------------------------



The first DDA code was written by Bernd. It's job was to simulate circuits, and this was
performed by a small Perl script which threw a few regexes onto the DDA file to convert it
to an executable C numeric simulation.

The idea was actually pretty brilliant as there was minimal code overhead and the iterative
solution would evventually bring a stable circuit. Circuit files look like



Would result in a C code which basically looks like

.. code-block:: c

    #include <stdio.h>
    #include <math.h>
    #include "dda.h"

    int main() {
        /* Constant declarations */
        double dt = 0.0005;
        double minus_dy0 = -1;
        double y0 = -1;

        /* Initial value definitions */
        double t = 0;
        double y = -y0;

        /* Scratch variables */
        double __dyold_minus_dy[6] = {minus_dy, minus_dy, minus_dy, minus_dy, minus_dy, minus_dy, };
        double __dyold_t[6] = {t, t, t, t, t, t, };
        double __dyold_y[6] = {y, y, y, y, y, y, };

        /* Variable definitions */
        double fix_minus_dy = 0.;

        /* Auxiliary variable definitions */
        unsigned int __i;

        /* Integration loop */
        for (__i = 0; __i < 10000; __i++) {
            __integrate(&t, 1, dt, __dyold_t);;
            __integrate(&minus_dy, y, dt, __dyold_minus_dy);;
            __integrate(&y, minus_dy, dt, __dyold_y);;
           printf("%.12g %.12g \n", y, t);
        }
        
        return 0;
    }


However, we found out that even with slightly more challenging circuits (kind of *border
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

