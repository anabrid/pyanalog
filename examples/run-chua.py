#!/usr/bin/env python3

import os

def sh(cmd):
    print(cmd)
    if os.system(cmd): raise ValueError(f"FAILED: {cmd}")

#base = "unscaled_chua"
base = "chua"

sh(f"python -m dda  {base}.dda C > {base}.cpp")
sh(f"g++ --std=c++20 -o {base}.out {base}.cpp")
sh(f"./{base}.out --max_iterations=100000 --modulo_write=10 > data.out")

from pylab import *

data = genfromtxt("data.out", names=True)

x,y,z = data["x"], data["y"], data["z"]

ion()

plot(x,y,lw=0.7)

## alternatively, we can plot something which
## alternates color by the z value:
# scatter(x,y,c=z)

savefig("chua.pdf")
