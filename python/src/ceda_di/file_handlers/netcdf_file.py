import netCDF4


from ceda_di.file_handlers.generic_file import GenericFile
from ceda_di.metadata import product

class   NetCdfFile(GenericFile):
    """
    Simple class for returning basic information about the content
    of an NetCDF file.
    """

    def __init__(self, file_path, level):
        GenericFile.__init__(self, file_path, level)

    def get_handler_id(self):
        return self.handler_id

    def phenomena(self):

        """
        Construct list of Phenomena based on variables in NetCDF file.
        :returns : List of metadata.product.Parameter objects.
        """

        try:
            with netCDF4.Dataset(self.file_path) as netcdf_object:
                phens = []
                for v_name, v_data in netcdf_object.variables.iteritems():
                    phen = product.Parameter(v_name, v_data.__dict__)
                    phens.append(phen)

                return phens
        except Exception:
            return None

    def get_properties_netcdf_level2(self):
        """
        Wrapper for method phenomena().
        :returns:  A dict containing information compatible with current es index level 2.
        """

        #Get basic file info.
        file_info = self.get_properties_generic_level1()

        if file_info is not None:

            self.handler_id = "Netcdf handler level 2."

            netcdf_phenomena = self.phenomena()

            if netcdf_phenomena is None:
                return None

            phenomena_list = []
            var_id_dict = {}
            phenomenon_parameters_dict = {}

            for item in netcdf_phenomena:           #get all parameter objects.

                name = item.get_name()               #get phenomena name.

                var_id_dict["name"] = "var_id"
                var_id_dict["value"] = name

                list_of_phenomenon_parameters = item.get()
                list_of_phenomenon_parameters.append(var_id_dict.copy())
                phenomenon_parameters_dict["phenomenon_parameters"] = list_of_phenomenon_parameters

                phenomena_list.append(phenomenon_parameters_dict.copy())

                var_id_dict.clear()
                phenomenon_parameters_dict.clear()


            file_info["phenomena"] = phenomena_list


            return file_info

        else:
            return self.get_properties_generic_level2()

    def get_properties(self):

        if self.level == "1":
            return self.get_properties_generic_level1()
        elif self.level == "2":
            return self.get_properties_netcdf_level2()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass
