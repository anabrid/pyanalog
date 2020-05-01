#!/usr/bin/env python3

from pylab import *
ion()

data = genfromtxt("result.dat", loose=True, invalid_raise=False)
x,z,t = data.T

# "fit" time
dt = average(diff(t)[:30]
tp = arange(len(x))*dt

plot(tp, x)
plot(tp, z)
