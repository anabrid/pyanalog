#!/bin/bash
#
# Copyright (c) 2020 anabrid GmbH
# Contact: https://www.anabrid.com/licensing/
#
# This file is part of the examples of the PyAnalog toolkit.
#
# ANABRID_BEGIN_LICENSE:GPL
# ANABRID_END_LICENSE
#

# or something like python -m fpaa
FPAA=../../fpaa/fpaa.py

base=$(basename $<)

# comment out this line if you want to skip image making
DO_IMAGES="-p $(base).png"

ARCH=-a Example-Arch.yml

%.out: %.yml
	@$(FPAA) -v $(ARCH) $(DO_IMAGES) $(base).yml > $(base).out 2>$(base).err && echo "$^" || echo "$^ [FAILURE]"

ALL_YMLS :=  $(patsubst %.yml,%.out,$(wildcard *.yml))

all: $(ALL_YMLS)

.PHONY = clean

clean:
	rm -f *.out *.err *.png

