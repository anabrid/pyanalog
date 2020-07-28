# Test Makefile to simplify some works...

MODULES := dda fpaa hycon
.PHONY: all doc

doc: 
	cd doc && $(MAKE) -j html dirhtml text

doctest:
	pytest --doctest-modules --pyargs dda  -v
	pytest --doctest-modules --pyargs hycon  -v
	# all other modules don't have useful tests anyway

test: 
	$(MAKE) doctest
	
clean:
	@find -type d -iname __pycache__ | xargs rm -r
