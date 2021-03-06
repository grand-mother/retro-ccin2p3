#!/usr/bin/env python

# Prune obsolete site packages at CC
import sys
exclude = "/usr/local/python/python-2.7/lib/python2.7/site-packages"
sys.path = [v for v in sys.path if not (exclude in v)]

import cPickle as pickle

import numpy
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from matplotlib.colors import LogNorm


from grand_tour import Topography


# Get the topography handle
topo = Topography(latitude=42.1, longitude=86.3, path="share/topography",
                  stack_size=49)

# Load the trigger map
#file="/home/martineau/GRAND/GRAND/data/massProd/HS1/jsons.triggers.p"
file="share/jsons_f50200.triggers.p"
with open(file, "rb") as f:
    n, latitude, longitude, rate = pickle.load(f)

# Compute the topography
h = numpy.zeros(rate.shape)
for i, la in enumerate(latitude):
    for j, lo in enumerate(longitude):
        h[i, j] = topo.ground_altitude(la, lo, geodetic=True)

# Show the map
try:
    plt.style.use("deps/mplstyle-l3/style/l3.mplstyle")
except:
    pass


plt.figure()
norme = colors.Normalize(vmin=0,vmax=numpy.max(h))
plt.contour(longitude, latitude, h, 10, cmap="terrain",norm=norme)
plt.pcolor(longitude, latitude, rate, cmap="nipy_spectral", alpha=0.5)
plt.colorbar()
plt.xlabel(r"longitude (deg)")
plt.ylabel(r"latitude (deg)")
plt.title(r"trigger rate (a$^{-1}$ / deg$^2$)")
plt.savefig("trigger-rate-map.png")
plt.show()
