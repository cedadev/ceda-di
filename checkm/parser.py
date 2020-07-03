import os
import re

import requests
import json

from ceda_di.index import BulkIndexer


def splitexts(path, exts=None):
    """
    Split each extension of a given file (.tar.gz, .tar, .pp, etc).
    """
    exts = []
    ext = os.path.splitext(path)
    while True:
        if len(ext[1]) < 1:
            break
        else:
            exts.append(ext[1])
            ext = os.path.splitext(ext[0])
    exts.reverse()
    return (path, exts)


class LogItem(object):
    """
    Simple class to construct a dictionary from log metadata.
    """
    def __init__(self, path, checksum, size, modified):
        self.metadata = {
            "path": path,
            "checksum": checksum,
            "size": size,
            "modified": modified,
            "extension": splitexts(path)[1],
            "name": os.path.basename(path)
        }

    def get_properties(self):
        return json.dumps(self.metadata)


class LogFile(object):
    """
    Contains methods to extract file information from CheckM log files.
    """
    def __init__(self, path, spot_mappings_url=None):
        self.path = path
        if spot_mappings_url:
            self.spot_mappings = self.get_mappings(spot_mappings_url)

    def get_mappings(self, url):
        """
        Fetch mappings in the format:
            'storage_pot /badc/path/to/data'
        Then split them and then return a dict with key:value pairs.

        :param url: The URL containing a list of directory mappings.
        :returns: A dict containing directory mappings for storage pots.
        """
        spot_paths = None
        req = requests.get(url)
        if req.status_code == 200:
            spot_paths = {l[0]: l[1] for l in
                          [line.split(" ") for line in req.text.splitlines()
                           if len(line) > 0]}

        return spot_paths

    def seek_through_comments(self, stream):
        """
        :param stream: An open file-like object.
        :returns path:
        """
        path = None
        for line in stream:
            if line.startswith("#"):
                match = re.match("# scaning path (?P<path>.*)", line)
                if match:
                    path = match.groupdict()["path"]
            else:
                break
        return path

    def split_log_lines(self, stream, delim, path_prefix=None):
        """
        :param stream: An open file-like object.
        :param delim: Character to split lines on.
        :path_prefix: Prefix to prepend to path.
        """
        for line in stream:
            path, _, checksum, size, date = line.split(delim)

            if path_prefix:
                path = os.path.join(path_prefix, path)

            log_items = [i.rstrip() for i in [path, checksum, size, date]]
            log_items[2] = int(log_items[2])

            yield log_items

    def get_entries(self):
        """
        Index log entries into an Elasticsearch installation.
        """
        prefixes = self.spot_mappings
        with open(self.path, 'r') as f:
            prefix_key = self.seek_through_comments(f).rsplit("/", 1)[-1]
            prefix = prefixes[prefix_key]

            for ln in self.split_log_lines(f, "|", prefix):
                yield LogItem(*ln).get_properties()

config = {
    "es-host": "fatcat-test.jc.rl.ac.uk",
    "es-port": 9200,
    "es-index": "checkm_test",
    "es-mapping": "file",
    "es-index-settings": "./index_settings.json"
}

infodb = "http://cedadb.ceda.ac.uk/fileset/download_conf/"
with BulkIndexer(config, 10000) as bi:
    log = LogFile("./checkm.ukmo-um.20141017-2142.log", infodb)
    for log_item in log.get_entries():
        bi.add_to_index_pool(log_item)
