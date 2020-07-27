.. _code-testing:

Code testing in PyDDA
=====================

This small code is still quite alpha, but we can easily do a number of tests
without much extra work:

* Doctests are super simple to approach, they are just embedded in the
  documentation. We attemp to have all doctest working :-)
* Acceptance/Integration tests: We can easily provide some DDA files
  where we know the solution analytically. It should be a useful exercise
  both for readers and testers to run these examples.
  This is on the TODO list


How to run doctests on the whole package
----------------------------------------

Use `pytest <https://docs.pytest.org/>`_ as a slim frontend for the python
doctest builtin:

::

    $ pytest-3 --doctest-modules --pyargs dda  -v


