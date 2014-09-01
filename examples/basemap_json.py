#! /usr/bin/env python

import json
import matplotlib
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap

font = {
    'family' : 'sans-serif',
    'size'   : 4
}

matplotlib.rc('font', **font)

with open("core_faam_20110902_v004_r1_b638_1hz.json", 'r') as f:
    data = json.loads(f.read())

m = Basemap(projection='gall',
            resolution='c',
            llcrnrlon=-180,
            llcrnrlat=-90,
            urcrnrlon=180,
            urcrnrlat=90)

m.drawcoastlines()
m.fillcontinents(color='coral',lake_color='aqua')
m.drawmapboundary(fill_color='aqua')

xs = [c[0] for c in data["spatial"]["geometries"]["coordinates"]]
ys = [c[1] for c in data["spatial"]["geometries"]["coordinates"]]
m.plot(xs, ys, lw=0.5, latlon=True)

plt.savefig("out.png", dpi=320, bbox_inches='tight')
