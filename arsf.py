#! /usr/bin/env python

import json
import multiprocessing
import os
import time
import bilparse.bilfile as libbil


def get_bil_nav(header_fname):
    b = libbil.BilFile(header_fname)
    b.calc_from_yb()
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

    procs = []  # List of processes
    for root, dirs, files in os.walk("/neodc/arsf/2011/"):
        for f in files:
            if root.endswith("navigation"):
                if (f.endswith(".hdr") and ("qual" not in f)):
                    header_fname = os.path.join(root, f)
                    print(header_fname)

                    p = multiprocessing.Process(target=get_bil_nav,
                                                args=(header_fname,))
                    procs.append(p)

                    while len(procs) > 10:
                        procs = [x for x in procs if (x.exitcode is None)]
                        time.sleep(0.1)

                    p.start()
                    p.join()
