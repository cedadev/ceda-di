#! /usr/bin/env python


class _geospatial(object):
    def __init__(self):
        exception = \
            "\"_datafile\" is an abstract base class and is intended" + \
            "to be used as an interface for EUFAR data files ONLY."

        raise NotImplementedError(exception)

    def get_geospatial_dict(self):
        self.__init__()
