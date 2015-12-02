import cf


from ceda_fbs.file_handlers.generic_file import GenericFile

class PpFile(GenericFile):
    """
    Simple class for returning basic information about the content
    of an PP file.
    """

    def __init__(self, file_path, level):
        GenericFile.__init__(self, file_path, level)

    def get_handler_id(self):
        return self.handler_id

    def phenomena(self):

        """
        Construct list of Phenomena based on variables in pp file.
        :returns : List of phenomena.
        """
        phenomenon_attr = {}
        phenomena_list = []
        phenomenon_parameters_dict = {}
        try:
            phenomena = cf.read(self.file_path)
            number_of_phenomena = len(phenomena)
            found = set()
            #For all phenomena.
            for i in range(0, number_of_phenomena):
                phen = phenomena[i]
                list_of_phenomenon_parameters = []
                list_of_phenomenon_parameters_t = []

                #For every phenomenon.
                dict_of_phenomenon_prop = phen.properties
                keys = dict_of_phenomenon_prop.keys()
                for key in keys:
                    value = str(dict_of_phenomenon_prop[key])

                    phenomenon_attr["name"] = key
                    phenomenon_attr["value"] = value
                    list_of_phenomenon_parameters.append(phenomenon_attr.copy())
                    #phenomenon_attr.clear()

                    list_of_phenomenon_parameters_t.append((key, value))

                #Also add var_id
                """
                phenomenon_attr["name"] = "var_id"
                if "name" in keys:
                    phenomenon_attr["value"] = str(dict_of_phenomenon_prop["name"])
                else:
                    phenomenon_attr["value"] = "None"

                #Attributes of phenomenon.
                list_of_phenomenon_parameters.append(phenomenon_attr.copy())
                phenomenon_attr.clear()
                """

                #Dict of phenomenon attributes.
                phenomenon_parameters_dict["phenomenon_parameters"] = list_of_phenomenon_parameters
                list_of_phenomenon_parameters_tt = tuple(list_of_phenomenon_parameters_t)


                if list_of_phenomenon_parameters_tt not in found:
                    found.add(list_of_phenomenon_parameters_tt)
                    #list of phenomenon.
                    phenomena_list.append(phenomenon_parameters_dict.copy())
                    phenomenon_parameters_dict.clear()
                else:
                    phenomenon_parameters_dict.clear()

            return phenomena_list
        except Exception:
            return None

    def get_properties_pp_level2(self):
        """
        Wrapper for method phenomena().
        :returns:  A dict containing information compatible with current es index level 2.
        """

        #Get basic file info.
        file_info = self.get_properties_generic_level1()

        if file_info is not None:

            self.handler_id = "pp handler level 2."
            #level 2
            pp_phenomena = self.phenomena()

            if pp_phenomena is None:
                return file_info

            file_info["phenomena"] = pp_phenomena

            return file_info

        else:
            return None

    def get_properties_pp_level3(self):
        res = self.get_properties_pp_level2()
        self.handler_id = "pp handler level 3."
        return res

    def get_properties(self):

        if self.level == "1":
            return self.get_properties_generic_level1()
        elif self.level == "2":
            return self.get_properties_pp_level2()
        elif self.level == "3":
            return self.get_properties_pp_level3()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass
