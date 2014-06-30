#! /usr/bin/env python

import lib_cedata.bilfile as bilfile
import matplotlib.pyplot as plt
import multiprocessing
import os


def draw_diagram(data):
    times = []
    low_hr = high_hr = None
    for key in data.keys():
        per_file = data[key]

        # Start times of each flight (per-day)
        t = int(per_file["time"][0]) % 86400
        hour, minute = divmod(t, 3600)
        times.append(hour)

        if low_hr is None or hour < low_hr:
            low_hr = hour
        if high_hr is None or hour > high_hr:
            high_hr = hour

    plot_range = (high_hr - low_hr)
    plt.hist(times, bins=plot_range, alpha=0.5)
    plt.title("ARSF flights/times")
    plt.xlabel("Time (hour of day)")
    plt.ylabel("Frequency")
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
    for root, dirs, files in os.walk("/neodc/arsf/2012", topdown=True):
        if root.endswith("navigation"):
            for f in files:
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
    draw_diagram(fdata)
