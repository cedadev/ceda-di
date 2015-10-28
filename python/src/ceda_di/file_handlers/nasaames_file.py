from generic_file import GenericFile
from ceda_di.metadata import product
import nappy


class NASAAmesFile(GenericFile):

    def __init__(self, file_path, level):
        GenericFile.__init__(self, file_path, level)

    def get_handler_id(self):
        return self.handler_id

    def get_parameters(self):

        try:
            na = nappy.openNAFile(self.file_path)

            variables = {}
            for v in na.getVariables():
                variables.update({
                    v[0]: {
                        "name": v[0],
                        "units": v[1]
                    }
                })

            variables = [product.Parameter(k, other_params=v) for (k, v) in variables.iteritems()]
            return variables
        except Exception:
            return None

    def get_properties_nanaames_level2(self):

        nasaames_phenomena = self.get_parameters()

        if nasaames_phenomena is not None:

            #Get basic file info.
            file_info = self.get_properties_generic_level1()

            self.handler_id = "Nasaames handler level 2."

            #List of phenomena
            phenomena_list = []
            var_id_dict = {}
            phenomenon_parameters_dict = {}

            for item in nasaames_phenomena :           #get all parameter objects.

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

        else :
            return self.get_properties_generic_level2()

    def get_properties(self):

        if self.level == "1" :
            return self.get_properties_generic_level1()
        elif self.level  == "2" :
            return self.get_properties_nanaames_level2()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass
