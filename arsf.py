#! /usr/bin/env python

import json
import multiprocessing
import os
import time
import lib_bil.bilfile as bilfile


def reprint(line):
    # http://stackoverflow.com/a/12586667
    CURSOR_UP = '\x1b[1A'
    ERASE_LINE = '\x1b[2K'
    print("%s%s%s" % (CURSOR_UP, ERASE_LINE, line))


def get_bil_nav(header_fname):
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

    output = format("out/%s.json" %
                    (os.path.splitext(os.path.basename(header_fname))[0]))

    with open(output, 'w') as out:
        out.write(json.dumps(swath_path, indent=4))


if __name__ == '__main__':
    try:
        os.mkdir("out")
    except OSError:
        pass

    # Indexing
    data_files = []  # List of viable data files
    procs = []  # List of processes
    for root, dirs, files in os.walk("/neodc/arsf/2011/"):
        for f in files:
            if root.endswith("navigation"):
                if (f.endswith(".hdr") and ("qual" not in f)):
                    header_fpath = os.path.join(root, f)
                    data_files.append(header_fpath)
                    reprint("%d files indexed." % (len(data_files)))

    # Process the header files
    print()
    for header_fpath in data_files:
        reprint("Processing: %s" % (os.path.basename(header_fpath)))
        p = multiprocessing.Process(target=get_bil_nav,
                                    args=(header_fpath,))
        procs.append(p)

        while len(procs) > 10:
            procs = [x for x in procs if (x.exitcode is None)]
            time.sleep(0.1)

        p.start()
