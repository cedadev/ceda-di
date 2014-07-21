class _geospatial(object):
    def __init__(self):
        exception = \
            "\"_datafile\" is an abstract base class and is intended" + \
            "to be used as an interface for EUFAR data files ONLY."

        raise NotImplementedError(exception)

    def get_file_level(self, fpath):
        file_level = {
            "filename": os.path.basename(fpath),
            "path": self.path,
            "size": os.stat(fpath).st_size,
        }

	def get_geospatial(self):
        self.__init__()

    def get_temporal(self):
        self.__init__()

    def get_parameters(self):
        self.__init__()