#!/usr/bin/env python

"""
find_indexed_files.py
=====================

(run "find_indexed_files.py -h" to view help)

"""

# Standard library imports
import os
import argparse

# Third-party imports
from elasticsearch import Elasticsearch


def parse_args():
    """
    Parses command line arguments.
    Returns parser object: argparse.ArgumentParser
    """
    parser = argparse.ArgumentParser(description="Finds files that have and haven't been indexed in Elasticsearch.")
    parser.add_argument("-i", "--index", required=True,
                      help="The full path to the elasticsearch index (e.g. 'jasmin-es1.ceda.ac.uk:9200/sentinel/geo_metadata')") 
    parser.add_argument("-d", "--directory", required=True,
                      help="The directory under which to look for files (recursively).")
    config = parser.parse_args()
    return config 


def build_file_list(path):
    "Return a list of files found under ``path``."
    file_list = []

    for root, _, files in os.walk(path, followlinks=True):
        for each_file in files:
            file_list.append(os.path.join(root, each_file))

    return file_list


def write_list_to_file(file_list, filename):
    "Write a list of items to a file ``filename``."
    with open(filename, 'w') as writer:

        for item in file_list:
            writer.write("%s\n" % item)


def open_connection(cfg):
    "Open, and return, a connection to an Elasticsearch index."
    host, port = cfg.index.split("/")[0].split(":")[:2]
    return Elasticsearch(hosts=[{"host": host, "port": port}])


def search_database_for_files(cfg):
    "Searches Elasticsearch index for files under directory given in config."
    es_conn = open_connection(cfg)
    _, es_index, es_type = cfg.index.split("/")

    directory = cfg.directory
    file_list = build_file_list(directory)

    files_found = len(file_list)
    file_not_found_list = []

    print "Directory: {}".format(directory)
    print "Number of files found: {}".format(files_found)

    files_indexed = 0
    files_not_indexed = 0 

    for filename in file_list:
        query = { "query": { "matchPhrase" : { "file.path" : filename } } }

        res = es_conn.search(index=es_index, doc_type=es_type, body=query,
                             request_timeout=60, size = 10000)

        hits = res[u'hits'][u'hits']

        if len(hits) > 0:
            files_indexed = files_indexed + 1
        else:
            files_not_indexed = files_not_indexed + 1
            file_not_found_list.append(filename)


    print "Number of files indexed: {}".format(files_indexed)
    print "Number of files not indexed: {}".format(files_not_indexed)

    print "File \"files_not_found.txt\" created and contains the files not found in the index."
    write_list_to_file(file_not_found_list, "files_not_found.txt")


def main(directory=None):
    "Main script."
    config = parse_args()
    search_database_for_files(config)


if __name__ == "__main__":

    main()
