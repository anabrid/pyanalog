.. _dda-rationale:

A rationale about DDA
=====================

The first DDA code was written by Bernd. It's job was to simulate circuits, and this was
performed by a small Perl script which threw a few regexes onto the DDA file to convert it
to an executable C numeric simulation.

The idea was actually pretty brilliant as there was minimal code overhead and the iterative
solution would evventually bring a stable circuit. Circuit files look like

.. code-block:: python

    dt = const(0.0005)
    t = int(1, dt)
    y0  = const(-1)
    minus_dy0 = const(-1)

    minus_dy = int(y, dt, minus_dy0)
    y        = int(minus_dy, dt, y0)

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

