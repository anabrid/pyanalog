#!/usr/bin/bash
for x in *.yml; do
	base=../circuits-compiled/$(basename ${x/.yml/}) # without dirname, without suffix
	DO_IMAGES="-p $base.png" # comment out this line if you want to skip
	( ../pyFPAA/compile.py -v -a AP-M1-Mini $DO_IMAGES $x \
        > $base.out 2>$base.err ) && echo "$x" || echo "$x [FAILURE]"
done;
