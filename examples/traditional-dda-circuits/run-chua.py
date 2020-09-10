#!/usr/bin/env python3
#
# Copyright (c) 2020 anabrid GmbH
# Contact: https://www.anabrid.com/licensing/
#
# This file is part of the examples of the PyAnalog toolkit.
#
# ANABRID_BEGIN_LICENSE:GPL
# Commercial License Usage
# Licensees holding valid commercial anabrid licenses may use this file in
# accordance with the commercial license agreement provided with the
# Software or, alternatively, in accordance with the terms contained in
# a written agreement between you and Anabrid GmbH. For licensing terms
# and conditions see https://www.anabrid.com/licensing. For further
# information use the contact form at https://www.anabrid.com/contact.
# 
# GNU General Public License Usage
# Alternatively, this file may be used under the terms of the GNU 
# General Public License version 3 as published by the Free Software
# Foundation and appearing in the file LICENSE.GPL3 included in the
# packaging of this file. Please review the following information to
# ensure the GNU General Public License version 3 requirements
# will be met: https://www.gnu.org/licenses/gpl-3.0.html.
# ANABRID_END_LICENSE
#


import os

def sh(cmd):
    print(cmd)
    if os.system(cmd): raise ValueError(f"FAILED: {cmd}")

#base = "unscaled_chua"
base = "chua"

N = int(5e6)
modulo_write = 30
iterations = N * modulo_write
variables = ["x", "y", "z"]

needs_recompile = True
if needs_recompile:
    sh(f"python3 -m dda  {base}.dda C > {base}.cpp")
    sh(f"g++ --std=c++17 -O3 -o {base}.out {base}.cpp")
sh(f"./{base}.out --max_iterations={iterations} --modulo_write={modulo_write} --binary_output=1 {' '.join(variables)} > data.out")

from numpy import *
from matplotlib.pylab import *

## reading from CSV:
#data = genfromtxt("data.out", names=True)
#x,y,z = data["x"], data["y"], data["z"]

## reading from binary:
print("Reading...")
data = fromfile("data.out", dtype="<f8").reshape(N, len(variables))
x,y,z = data.T

ion()

## naively plot:
# plot(x,y,lw=0.7)

## alternatively, we can plot something which
## alternates color by the z value:
# scatter(x,y,c=z)

## Do a density map:
print("Computing density map...")
H, xedges, yedges = histogram2d(x,y,bins=500)

H.T[H.T == 0] = min(H.T[H.T != 0]) # clip zeros
mat = log(H.T)

def show(mat):
    clf()
    imshow(mat, interpolation='nearest', origin='lower', 
        extent=[xedges[0], xedges[-1], yedges[0], yedges[-1]],
        cmap=cm.binary)
    colorbar()
    
def show2(mat):
    clf()
    ax = gca()
    from matplotlib.image import NonUniformImage
    #ax = fig.add_subplot(133, title='NonUniformImage: interpolated',
        #aspect='equal', xlim=xedges[[0, -1]], ylim=yedges[[0, -1]])
    im = NonUniformImage(ax, interpolation='bilinear')
    xcenters = (xedges[:-1] + xedges[1:]) / 2
    ycenters = (yedges[:-1] + yedges[1:]) / 2
    im.set_data(xcenters, ycenters, mat)
    ax.images.append(im)
    xlim(xedges[[0, -1]])
    ylim(yedges[[0, -1]])
    #plt.show()


show2(mat)



savefig("chua.pdf")
