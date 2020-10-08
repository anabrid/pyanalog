.. _installation:

Obtaining and installing PyAnalog
=================================

PyAnalog can be used without dependencies. Only make sure you use a *recent* Python 3
installation. We use `f-strings`, so at least Python 3.6 is required.

For more advanced usages, we recommend at least the following dependencies:

* `PyYAML <https://pyyaml.org/>`_, for a good experience of PyFPAA
* `SymPy <https://www.sympy.org/>`_, for more features of PyDDA

Obtaining the code
------------------

The code is currently developed in a *locked-down Gitlab installation* at
https://lab.analogparadigm.com/software/pyanalog. In order to access this repository,
you have to contact the authors/maintainers at http://www.anabrid.com
(refered to as *the analogians* in the following).

Recommended way of installation (developer machine setup)
---------------------------------------------------------

We recommend the following way of obtaining and installing the PyAnalog code
on your developer machine using *setuptools* by using the
`development mode <https://setuptools.readthedocs.io/en/latest/setuptools.html#development-mode>`_
(which creastes a user-wide softlink to the working copy):

.. code-block:: bash

    $ cd prefered/directory/for/code/of/the/analogians
    $ git clone git@lab.analogparadigm.com:software/pyanalog.git
    $ cd pyanalog
    $ python3 setup.py develop --user

After these steps you are ready to use import the pyanalog package modules from any
Python3 script anywhere on your system, but only *as your current user*:

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

   $ pip install git+ssh://git@lab.analogparadigm.com:software/pyanalog.git

This will automatically install all the dependencies from the ``requirements.txt`` file.

You can also add the flags ``--user`` for a per-user (instead of system wide) installation.
If you want to perform an upgrade on an existing installation, add the ``--upgrade``
flag.

Note that by using this installation method, you cannot easily make edits to the pyanalog
code itself. This is perfectly fine if you only want to use the library.

Other ways of installation/usage
--------------------------------

* You can also just checkout the repository, navigate to the root directory and open
  a python script from there. This way, you don't have to install anything but have
  the modules right in your ``PYTHONPATH``. This is really the easiest way of getting
  started if you don't want to mess around with ``pip`` or ``setup.py``.
* It is usually good practice to use *virtualenv*. Standard routines should apply
  for using pip within virtualenv.

