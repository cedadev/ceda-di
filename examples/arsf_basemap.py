#! /usr/bin/env python

import eufar.bilfile as bilfile
import matplotlib
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
import multiprocessing
import os


def draw_map(data):
    font = {'family' : 'sans-serif',
            'size'   : 4}
    matplotlib.rc('font', **font)

    lllat = lllon = urlat = urlon = None
    avg_lat = avg_lon = 0.0
    for key in data.keys():
        for lat in data[key]["lat"]:
            if lat > urlat or urlat is None:
                urlat = lat
            elif lat < lllat or lllat is None:
                lllat = lat

        for lon in data[key]["lon"]:
            if lon > urlon or urlon is None:
                urlon = lon
            elif lon < lllon or lllon is None:
                lllon = lon

        avg_lat += sum(data[key]["lat"])/len(data[key]["lat"])
        avg_lon += sum(data[key]["lon"])/len(data[key]["lon"])
    avg_lat /= len(data.keys())
    avg_lon /= len(data.keys())

    left = (avg_lon - 2)
    bottom = (avg_lat - 2)
    right = (avg_lon + 2)
    top = (avg_lat + 2)
    m = Basemap(projection='gall',
                resolution='f',
                llcrnrlon=left,
                llcrnrlat=bottom,
                urcrnrlon=right,
                urcrnrlat=top)
    m.shadedrelief()

    if data is not None:
        for key in data.keys():
            coords = data[key]
            xs = coords["lon"][0::100]
            ys = coords["lat"][0::100]
            lbl = os.path.basename(key).split("_nav_post_processed.bil.hdr")[0]
            m.plot(xs, ys, lw=0.5, latlon=True, label=lbl)
    
    plt.legend()
    plt.savefig("out.png", dpi=320, bbox_inches='tight')


def reprint(line):
    # http://stackoverflow.com/a/12586667
    CURSOR_UP = '\x1b[1A'
    ERASE_LINE = '\x1b[2K'
    print("%s%s%s" % (CURSOR_UP, ERASE_LINE, line))


def get_bil_nav(header_fname, multiproc_manager_dict):
    b = bilfile.BilFile(header_fname)
    bil = b.read_bil()

    swath_path = {
        "lines": b.hdr["lines"],
        "time": bil[0],
        "lat": bil[1],
        "lon": bil[2],
        "alt": bil[3],
        "roll": bil[4],
        "pitch": bil[5],
        "heading": bil[6]
    }

    multiproc_manager_dict[header_fname] = swath_path


def wait_for_processes(proc_list, nprocs=0):
    while len(proc_list) > nprocs:
        proc_list = [x for x in proc_list if (x.is_alive())]


if __name__ == '__main__':
    # Indexing
    data_files = []  # List of viable data files
    procs = []  # List of processes
    print("")
    for root, dirs, files in os.walk("/neodc/arsf/2011/EM10_06/EM10_06-2011_260_Italy/hyperspectral"):
        for f in files:
            if root.endswith("navigation"):
                if (f.endswith(".hdr") and ("qual" not in f)):
                    header_fpath = os.path.join(root, f)
                    data_files.append(header_fpath)
                    reprint("%d files indexed." % (len(data_files)))

    # Process the header files
    m = multiprocessing.Manager()
    fdata = m.dict()
    print("")
    for header_fpath in data_files:
        reprint("Processing: %s" % (os.path.basename(header_fpath)))
        p = multiprocessing.Process(target=get_bil_nav,
                                    args=(header_fpath, fdata,))

        wait_for_processes(procs, 4)
        procs.append(p)
        p.start()

    wait_for_processes(procs, 0)
    draw_map(fdata)
