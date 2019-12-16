#!/bin/bash
for x in *.yml; do
	base=${x/.yml/}
	../fpAA/compile.py -a AP-M1-Mini $x > $base.out 2>$base.err;
done;
