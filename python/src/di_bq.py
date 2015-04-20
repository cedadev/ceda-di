#!/usr/bin/env python
"""
`di_bq.py` is a wrapper around the standard ceda-di tools to help parallelise
the processing of files using a batch queue.

This tool has two main functions:
    * Generate lists of files to be processed in individual jobs by the queue
    * Dispatch archive processing jobs to the batch queue

Usage:
    di_bq.py (--help | --version)
    di_bq.py gen-list <input-dir> <file-list-output-dir> --num=<num>
    di_bq.py submit-jobs <dir-containing-file-lists> [--delete-after]

Options:
    --help              Show this screen.
    --version           Show version.
    --num               Number of paths to store in each file [default: 5000].
    --delete-after      Delete input files after job submission.
"""

import simplejson as json
import os

from docopt import docopt

from ceda_di import __version__  # Grab version from package __init__.py
import ceda_di.util.cmd as cmd


def dump_to_json(output_directory, seq, file_list):
    """
    Write the object specified in "file_list" to a JSON file list.

    :param str output_directory: The directory to write all of the files into.
    :param int seq: The sequence number of the file.
    :param list file_list: The list of files to serialise to JSON.
    """
    out_name = "{seq}.json".format(seq=seq)
    out_path = os.path.join(output_directory, out_name)

    with open(out_path, "w") as out_f:
        json.dump(file_list, out_f)


def construct_bsub_command(input_file_path):
    """
    """
    pass


def main():
    # Get arguments from command line
    args = cmd.sanitise_args(docopt(__doc__, version=__version__))

    if args["gen-list"]:
        # Set up variables from command-line parameters
        path = args["path-to-input-directory"]
        output_directory = args["dir-containing-file-lists"]
        max_files = args["--num"]
        seq = 0

        # Begin sweeping for files
        file_list = []
        for root, dirs, files in os.walk(path):
            for f in files:
                fp = os.path.join(root, f)
                file_list.append(fp)

                # Dump file paths to JSON document
                if len(file_list) > max_files:
                    seq += 1  # Increment file sequence number
                    dump_to_json(output_directory, seq, file_list)
                    file_list = []

                dump_to_json(output_directory, seq, file_list)
    elif args["submit-jobs"]:
        input_directory = args["dir-containing-file-lists"]

        for root, dirs, files in os.walk(input_directory):
            for f in files:
                fp = os.path.join(root, f)
                construct_bsub_command(fp)


if __name__ == "__main__":
    main()
