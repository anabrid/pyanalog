MODULES := dda fpaa hycon
.PHONY: all doc help

# Note: these tests only run when you have installed the pyanalog package
# on your local computer. Since this is not the case for the docker images, cf.
# htps://docs.pytest.org/en/stable/pythonpath.html#invoking-pytest-versus-python-m-pytest
#
# either use PYTEST=pytest
# or use python -m pytest, which has the advantage to have $PWD in 
# PYTHONPATH, so it works without having the package installed.
# See https://stackoverflow.com/a/34140498
PYTEST=python -m pytest

doc: 
	cd doc && $(MAKE) clean && $(MAKE) -j html dirhtml text

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

help:
	@cat Makefile
