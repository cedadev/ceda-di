class _geospatial(object):
    def __init__(self):
        exception = \
            "\"_geospatial\" is an abstract base class and is intended" + \
            "to be used as an OO interface for EUFAR data files ONLY."

        raise NotImplementedError(exception)

    def get_file_level(self, fpath):
        file_level = {
            "filename": os.path.basename(fpath),
            "path": fpath,
            "size": os.stat(fpath).st_size,
        }
        
        return file_level

	def get_geospatial(self):
	    self.__init__()

    def get_temporal(self):
        self.__init__()

    def get_parameters(self):
        self.__init__()
