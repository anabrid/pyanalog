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
   `at the github commit history <https://github.com/anabrid/pyanalog/commits/master>`_
   where there is a green checkmark at the tests (and not a red crossmark).
   I promise there will be releases/versions/tags soon :-)
   
Mac OS X-specific installation notes
------------------------------------

The following code block shows a minimal way how quickly to start on Mac OS X.
This assumes you have some C++ compiler available, e.g. from Xcode (Clang).

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

Note that with the Clang/LLVM compiler, you have to set ``--std=c++1z`` instead of 
``--std=c++17`` (as with GCC).

Microsoft Windows-specific installation notes
---------------------------------------------

On Windows, we have made best experiences with *MinGW* providing the compiler. Make sure
you add the installation directory to your PATH in order to be able to access the compiler
from everywhere (i.e. every terminal).

For the Python environment, you can install it from the Windows store (and use pip as usual)
or install an IDE such as *Spyder*. This is particularly handy because it provides also a
lean way to setup the developer machine. For instance, there is a menu item
*Tools/Current user environment variables...* which allows you to set the system wide
PATH. The ``HKEY_CURRENT_USER\Environment`` should, as a list, probably contain paths such
as

.. code-block::

    C:\MinGW\bin
    C:\Program Files\Spyder\Python

This way, you are fully flexible to use both the C compiler as well as the Python binaries
from everywhere. If you do not have a comfortable IDE, you might want to look into
*Powershell* as well as the new
`Windows Terminal <https://www.microsoft.com/de-de/p/windows-terminal/9n0dx20hk701#activetab=pivot:overviewtab>`_
which can be obtained in the Microsoft store for free.

While it is attractive to download the PyAnalog software as a ZIP file from Github, we
recommend you instead to install a proper Git client, such as the comprehensible
`Github Desktop <https://desktop.github.com>_` GUI. This way it is as easy as a single click
on *update* to obtain a more recent version of the PyAnalog code.

.. note::

   At Windows, we have experienced some hazzles with *UTF-16* encoded files. While we are
   working on getting more compatibility with the PyAnalog tools, you can convert any
   file to *UTF-8* by using such a  Powershell command:
   
   .. code-block::

       Get-Content nameOfYourFile.txt | Out-File -Encoding UTF8 nameOfYourFile-fixed.txt
   
   Also don't forget that Windows generally does not allow you to open files for writing while
   they are opened for reading. If you are used to the unix kind of dealing with files, this can
   make some steps more cumbersome and result in more copies of files.


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

