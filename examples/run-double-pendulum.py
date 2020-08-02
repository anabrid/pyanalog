#!/usr/bin/env python3

import os

def sh(cmd):
    print(cmd)
    if os.system(cmd): raise ValueError(f"FAILED: {cmd}")

# Run the double pendulum
sh("python -m dda  double-pendulum.dda C > double-pendulum.cpp")
sh("g++ --std=c++20 -o double-pendulum.out double-pendulum.cpp")
sh("./double-pendulum.out --max_iterations=30000 --modulo_write=10 > data.out")

from pylab import *

data = genfromtxt("data.out", names=True)

p1, p2 = data["p1"], data["p2"]
l1, l2 = 1, 1 # lengths of pendulums

x1 = l1*sin(p1)
y1 = l1*cos(p1)
x2 = l2*sin(p2) + x1
y2 = l2*cos(p2) + y1

ion()
plot(x1, y1)
plot(x2, y2)

savefig("double-pendulum.png")
