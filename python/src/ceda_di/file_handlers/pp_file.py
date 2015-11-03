import os
import cf
import inspect


from generic_file import GenericFile

class PpFile(GenericFile):
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
        :returns : List of phenomena.
        """
        phenomenon_attr = {}
        phenomena_list = []
        phenomenon_parameters_dict = {}
        try:
            phenomena = cf.read(self.file_path)
            number_of_phenomena = len(phenomena)
            #For all phenomena.
            for i in range(0, number_of_phenomena):
                phen = phenomena[i]
                list_of_phenomenon_parameters = []

                #For every phenomenon.
                dict_of_phenomenon_prop = phen.properties
                keys = dict_of_phenomenon_prop.keys()
                for key in keys:
                        phenomenon_attr["name"] = key
                        phenomenon_attr["value"] = str(dict_of_phenomenon_prop[key])

                        list_of_phenomenon_parameters.append(phenomenon_attr.copy())
                        phenomenon_attr.clear()

                #Also add var_id
                phenomenon_attr["name"] = "var_id"
                if "name" in keys:
                    phenomenon_attr["value"] = str(dict_of_phenomenon_prop["name"])
                else:
                    phenomenon_attr["value"] = "None"

                #Attributes of phenomenon.
                list_of_phenomenon_parameters.append(phenomenon_attr.copy())
                phenomenon_attr.clear()

                #Dict of phenomenon attributes.
                phenomenon_parameters_dict["phenomenon_parameters"] = list_of_phenomenon_parameters

                #list of phenomenon.
                phenomena_list.append(phenomenon_parameters_dict.copy())
                phenomenon_parameters_dict.clear()

            return phenomena_list
        except Exception as e:
            return None

    def get_properties_netcdf_level2(self):
        """
        Wrapper for method phenomena().
        :returns:  A dict containing information compatible with current es index.
        """

        pp_phenomena = self.phenomena()

        if pp_phenomena is not None:

            #Get basic file info.
            file_info = self.get_properties_generic_level1()

            self.handler_id = "pp handler level 2."
            file_info["phenomena"] = pp_phenomena

            return file_info

        else:
            return self.get_properties_generic_level2()

    def get_properties(self):

        if self.level == "1":
            return self.get_properties_generic_level1()
        elif self.level  == "2":
            return self.get_properties_netcdf_level2()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass
