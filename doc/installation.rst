.. _installation:

Obtaining and installing PyAnalog
=================================

PyAnalog can be used on a "vanilla" Python installation without any dependencies.
Only make sure you use a *recent* Python 3 installation:
We use ``f-strings``, so at least Python 3.6 is required.

In order to use some of the advanced features, we recommend to install the following
Python packages:

* `PyYAML <https://pyyaml.org/>`_, for the intended usage of :ref:`PyFPAA <fpaa>`
* `SymPy <https://www.sympy.org/>`_, for the :ref:`SymPy/Computer Algebra interface <cas>` of PyDDA
* `SciPy <http://www.scipy.org/>`_, for the :ref:`SciPy interface <scipy>` of PyDDA.
  Furthermore, some additioanl postprocessing tools, as well as unit tests and examples of PyDDA
  require `NumPy <https://numpy.org/>`_ and `Matplotlib <https://matplotlib.org/>`_ to be installed.

Obtaining the code
------------------

The PyAnalog code is public available at https://github.com/anabrid/pyanalog.
Furthermore, we maintain an in-house (private) mirror at 
https://lab.analogparadigm.com/software/pyanalog. You don't need access to the later repository
right now.

..
    TODO: In our internal Gitlab, we currently have Continous Integration (CI) and also
    a bug tracker. This should be improved.
    
    In order to access this repository,
    you have to contact the authors/maintainers at http://www.anabrid.com
    (refered to as *the analogians* in the following).

.. note::

   We try to keep the `master branch <https://github.com/anabrid/pyanalog/commits/master>`_
   in a working condition. If things do not work, you might want to checkout the last
   working commit in the master. You can recognize it 
   `at the github commit history <<https://github.com/anabrid/pyanalog/commits/master>`_
   where there is a green checkmark at the tests (and not a red crossmark).
   I promise there will be releases/versions/tags soon :-)
   
Minimal starter (Mac OS X)
--------------------------

.. code-block:: bash
    $ pip3 install scipy numpy matplotlib # the only dependencies you really need
    $ git clone https://github.com/anabrid/pyanalog.git
    $ cd pyanalog
    $ python3 setup.py develop --user # this way you can import the python module from anwhere
    $ cd examples/traditional-dda-circuits
    $ python3 -m dda chua.dda c > chua.cpp
    $ c++ --std=c++1z chua.cpp     # c++1z-Standard is specific to Mac / clang
    $ ./a.out > chua.dat
    $ gnuplot etc...

    
Recommended way of installation (developer machine setup)
---------------------------------------------------------

We recommend the following way of obtaining and installing the PyAnalog code
on your developer machine using *setuptools* by using the
`development mode <https://setuptools.readthedocs.io/en/latest/setuptools.html#development-mode>`_
(which creastes a user-wide softlink to the working copy):

.. code-block:: bash

    $ cd prefered/directory/for/code/of/the/analogians
    $ git clone https://github.com/anabrid/pyanalog.git # this works always
    $ git clone git@github.com:anabrid/pyanalog.git     # use this if you are experienced at github
    $ cd pyanalog
    $ python3 setup.py develop --user

After these steps you are ready to use import the pyanalog package modules from any
Python3 script anywhere on your system, but only *as your current user*. The installation
is successful when you can for instance ``import dda`` somewhere:

.. code-block::

    $ python3
    Python 3.8.6 (default, Sep 30 2020, 04:00:38)
    [GCC 10.2.0] on linux
    Type "help", "copyright", "credits" or "license" for more information.
    >>> import dda
    >>> dda.Symbol("foo")
    foo

User (non-developer) installation
---------------------------------

If you want to install the package, just call ``pip install`` or ``python3 setup.py install``
in the repository root directory after cloning or without any cloning by just running:

.. code-block:: bash

   $ pip install git+ssh://git@github.com:anabrid/pyanalog.git

This will automatically install all the dependencies from the ``requirements.txt`` file.

You can also add the flags ``--user`` for a per-user (instead of system wide) installation.
If you want to perform an upgrade on an existing installation, add the ``--upgrade``
flag.

Note that by using this installation method, you cannot easily make edits to the pyanalog
code itself. This is perfectly fine if you only want to use the library.

.. note::

   Since the overall code is still subject to heavy changes, you should also opt in
   for the developer machine setup installation method if you do not indend to work
   on the PyAnalog code. This is for easier updating or changing versions with ``git``
   without having to perform a fresh installation. Basically, with the development
   installation way, you can change/update/downgrade the PyAnalog code and immediately
   profit in your applications.


Other ways of installation/usage
--------------------------------

* You can also just checkout the repository, navigate to the root directory and open
  a python script from there. This way, you don't have to install anything but have
  the modules right in your ``PYTHONPATH``. This is really the easiest way of getting
  started if you don't want to mess around with ``pip`` or ``setup.py``.
* It is usually good practice to use *virtualenv*. Standard routines should apply
  for using pip within virtualenv.

