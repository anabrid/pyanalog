# Test Makefile to simplify some works...

MODULES := dda fpaa hycon
.PHONY: all doc

doc: 
	cd doc && $(MAKE) -j html dirhtml text

doctest:
	pytest --doctest-modules --pyargs dda  -v
	pytest --doctest-modules --pyargs hycon  -v
	# all other modules don't have useful tests anyway
	
unittests:
#	(actually these are integration/acceptance tests)
#	Note: these tests only run when you have installed the pyanalog package
#	on your local computer. Since this is not the case for the docker images, cf.
#	https://docs.pytest.org/en/stable/pythonpath.html#invoking-pytest-versus-python-m-pytest
#	try instead:
#	#python -m pytest tests
	pytest -v

test: 
	$(MAKE) doctest unittests
	
clean:
	@find -type d -iname __pycache__ | xargs rm -r
