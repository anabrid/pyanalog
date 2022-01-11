# This is a small makefile for PyAnalog. It collects a number of frequent
# tasks, also used by the CI. But actually this is not the right place if
# you just want to get started with PyAnalog. Read the docs instead.
# This is a python script code base, there is basically nothing to "build"
# or "compile" before use. That is, the code is "ready to use" as is, if
# you get managed with the proper paths etc. at usage. So please go on
# and read doc/installation.rst

MODULES := dda fpaa hycon
.PHONY: all doc help install

# path to your python binary
PYTHON=python3

# Note: these tests only run when you have installed the pyanalog package
# on your local computer. Since this is not the case for the docker images, cf.
# htps://docs.pytest.org/en/stable/pythonpath.html#invoking-pytest-versus-python-m-pytest
#
# either use PYTEST=pytest
# or use python -m pytest, which has the advantage to have $PWD in 
# PYTHONPATH, so it works without having the package installed.
# See https://stackoverflow.com/a/34140498
PYTEST=$(PYTHON) -m pytest

doc: 
	cd doc && $(MAKE) clean && $(MAKE) -j html dirhtml latexpdf
	# also zip docs for download
	cd doc/_build && tar cvfz pyanalog-docs-html.tar.gz  html
	cd doc/_build && tar cvfz pyanalog-docs-latex.tar.gz latex

doctest:
	$(PYTEST) --doctest-modules --pyargs dda --ignore=dda/__main__.py  -v
	$(PYTEST) --doctest-modules --pyargs hycon  -v
	# all other modules don't have useful tests anyway
	
unittests:
#	(actually these are integration/acceptance tests)
	$(PYTEST) -v

test: 
	$(MAKE) doctest unittests
	
clean:
	@find -type d -iname __pycache__ | xargs rm -r
#	and for heavens sake, clean any mess in the git root...
	rm -rf *.exe *.out generated.cc

# this is the recommended way of ensuring Python can import the PyAnalog
# modules (such as `dda`) from anywhere. It won't install binaries on the
# user path, thought. See docs/installation.rst for details.
install:
	$(PYTHON) setup.py develop --user

help:
	@cat Makefile
