.. _installation:

Installation of PyDDA
=====================

PyDDA can be used without dependencies. Only make sure you use a *recent* Python 3
installation. We use `f-strings`, so at least Python 3.6 is required.

Obtaining the code
------------------

We don't yet deploy on PyPi or similar. Therefore, checkout the development
repository at https://lab.analogparadigm.com/koeppel/dda

Using the code: Short story
---------------------------

If you are lazy, just softlink the ``pydda`` directory wherever you need it.

However, we use setuptools and there is a super simple way of installing this
softlink user-wide by using
`development mode <https://setuptools.readthedocs.io/en/latest/setuptools.html#development-mode>`_:

.. code-block:: bash

    $ git clone git@lab.analogparadigm.com:koeppel/dda.git
    $ cd dda/PyDDA
    $ python3 setup.py develop --user


After these steps you are ready to use import the ``pydda`` from any Python3 script
anywhere on your system, but only *as your current user*.

If you want to install the package, just call ``pip install`` or ``python3 setup.py install``
in the ``PyDDA`` directory. This will then copy the code, so you should can delete
the repository checkout afterwards.

Requirements and dependencies: The long story
---------------------------------------------

- **Python >=3.6** is required.
- Some packages are recommended. See ``setup.py`` for the list of packages.

To be done: Write more about virtualenv and how to use pip to install the
(optional) dependencies.



