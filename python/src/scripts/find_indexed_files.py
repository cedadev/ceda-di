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


DEFAULT_ES_DETAILS = {'host': 'jasmin-es1.ceda.ac.uk', 'port': '9200', 'type': 'geo_metadata'}


def parse_args():
    """
    Parses command line arguments.
    Returns parser object: argparse.ArgumentParser
    """
    parser = argparse.ArgumentParser(description="Finds files that have and haven't been indexed in Elasticsearch.")
    parser.add_argument("-i", "--index", required=True,
                      help="The elasticsearch index (e.g. 'sentinel')")
    parser.add_argument("-d", "--directory", required=True,
                      help="The directory under which to look for files (recursively).")
    parser.add_argument("-e", "--extension", required=False, default=None,
                      help="The file extension (e.g. 'manifest' or 'nc') that should be matched.")
    parser.add_argument("-v", "--verbose", required=False, default=False, action="store_true",
                      help="Verbose logging: shows every file that is being checked.")
    config = parser.parse_args()
    return config 


def build_file_list(path, extension=None):
    """
    Return a list of files found under ``path``.
    If ``extension`` is defined then only return files that have that extension.
    """
    if extension and extension[0] != ".":
        extension = "." + extension
        
    file_list = []

    for root, _, files in os.walk(path, followlinks=True):
        for each_file in files:

            if not extension or each_file.endswith(extension):
                file_list.append(os.path.join(root, each_file))

    return file_list


def write_list_to_file(file_list, filename):
    "Write a list of items to a file ``filename``."
    with open(filename, 'w') as writer:

        for item in file_list:
            writer.write("%s\n" % item)


def open_connection(host, port):
    "Open, and return, a connection to an Elasticsearch index."
    return Elasticsearch(hosts=[{"host": host, "port": port}])


def _resolve_es_index_path(index):
    "Returns a valid URL path for the index."
    if index.startswith("http"):
        index = index.split(":")[1].strip("/")

    if index.startswith("jasmin"):
        host_port, es_index, es_type = index.strip("/").split("/")
        es_host, es_port = host_port.split(":")
        return es_host, es_port, es_index, es_type

    else:
        d = DEFAULT_ES_DETAILS
        return d['host'], d['port'], index, d['type']
  

def search_es_for_files(cfg):
    "Searches Elasticsearch index for files under directory given in config."
    es_host, es_port, es_index, es_type = _resolve_es_index_path(cfg.index)
    es_conn = open_connection(es_host, es_port)

    directory = cfg.directory
    file_list = build_file_list(directory, cfg.extension)

    files_found = len(file_list)
    file_not_found_list = []

    print "\nDirectory: {}".format(directory)
    print "Number of files found under directory: {}\n".format(files_found)
  
    files_indexed = 0
    files_not_indexed = 0 

    for filename in file_list:
        query = { "query": { "matchPhrase" : { "file.path" : filename } } }
        res = es_conn.search(index=es_index, doc_type=es_type, body=query,
                             request_timeout=60, size = 10000)

        hits = res[u'hits'][u'hits']

        if len(hits) > 0:
            files_indexed = files_indexed + 1
            if cfg.verbose: 
                print "File: {} ...is in index.".format(filename)
        else:
            files_not_indexed = files_not_indexed + 1
            file_not_found_list.append(filename)
            if cfg.verbose:
                print "File: {} ...NOT FOUND IN INDEX.".format(filename)


    print "\nNumber of files indexed: {}".format(files_indexed)
    print "Number of files not indexed: {}\n".format(files_not_indexed)

    if file_not_found_list:
        FNAME = "files_not_found.txt" 
        write_list_to_file(file_not_found_list, FNAME)
        print "Wrote file '%s' listing files not yet indexed." % FNAME
    else:
        print "Hooray. All files are in the index."


def main(directory=None):
    "Main script."
    config = parse_args()
    search_es_for_files(config)


if __name__ == "__main__":

    main()
