#!/usr/bin/env python3

from pylab import *
clf(); ion()

data = genfromtxt("y_t_eq_y_and_time.dat", loose=True, invalid_raise=False)
yt,t = data.T

data = genfromtxt("y_tt.dat", loose=True, invalid_raise=False)
ytt = data[:,0]

data = genfromtxt("y_ttt.dat", loose=True, invalid_raise=False)
yttt = data[:,0]

# "fit" time
dt = abs(average(diff(t)[:15]))
t = lambda y: arange(len(y))*dt

exact = exp(-t(yt))

plot(t(yt), yt, label="$y' = -y$")
plot(t(ytt), ytt, label="$y'' = +y$")
plot(t(yttt), yttt, label="$y''' = -y$")
plot(t(exact), exact, "--", label="Exact solution")

legend()

xlim(0,20)
title("Three ways of producing exp(-t) on an analog computer...")

tight_layout()

