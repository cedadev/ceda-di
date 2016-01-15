import cf
import fbs_lib.util as util


from fbs.file_handlers.generic_file import GenericFile

class PpFile(GenericFile):
    """
    Simple class for returning basic information about the content
    of an PP file.
    """

    def __init__(self, file_path, level, additional_param=None):
        GenericFile.__init__(self, file_path, level)
        self.FILE_FORMAT = "PP"
        self.additional_param = additional_param

    def get_handler_id(self):
        return self.handler_id

    def phenomena(self, phenomena):

        """
        Construct list of Phenomena based on variables in pp file.
        :returns : List of phenomena.
        """
        phenomenon_attr = {}
        phenomena_list = []
        phenomenon_parameters_dict = {}
        try:
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

                    if len(key) < util.NETCDF_MAX_PAR_LENGTH \
                       and len(value) < util.NETCDF_MAX_PAR_LENGTH:
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
            cf.TEMPDIR(self.additional_param)
            phenomena = cf.read(self.file_path)
            pp_phenomena = self.phenomena(phenomena)

            if pp_phenomena is None:
                return file_info

            file_info["phenomena"] = pp_phenomena

            return file_info

        else:
            return None

    def normalize_coord(self, coord):
        if coord > 180:
            coord = coord - 360
        return coord

    def get_properties_pp_level3(self):
         #Get basic file info.
        file_info = self.get_properties_generic_level1()

        if file_info is not None:

            self.handler_id = "pp handler level 2."
            #level 2
            cf.TEMPDIR(self.additional_param)
            phenomena = cf.read(self.file_path)
            pp_phenomena = self.phenomena(phenomena)

            if pp_phenomena is None:
                return file_info

            file_info["phenomena"] = pp_phenomena

            #geospatial data.
            list_max_lat = []
            list_min_lat = []
            list_max_lon = []
            list_min_lon = []
            for item in phenomena:
                dim_dict_lat = item.coords('lat')
                dim_dict_lon = item.coords('lon')
                for key in dim_dict_lat:
                    list_max_lat.append(float(str(item.coords('lat')[key].max()).split()[0]))
                    list_min_lat.append(float(str(item.coords('lat')[key].min()).split()[0]))

                for key in dim_dict_lon:
                    list_max_lon.append(float(str(item.coords('lon')[key].max()).split()[0]))
                    list_min_lon.append(float(str(item.coords('lon')[key].min()).split()[0]))

            max_lat = self.normalize_coord(max(list_max_lat))
            min_lat = self.normalize_coord(min(list_min_lat))
            max_lon = self.normalize_coord(max(list_max_lon))
            min_lon = self.normalize_coord(min(list_min_lon))

            file_info["spatial"] = {'coordinates': {'type': 'envelope', 'coordinates': [[max_lat, max_lon], [max_lon, min_lon]]}}


            return file_info

        else:
            return None


        res = self.get_properties_pp_level2()
        #ok lets add geospatial information.
        self.handler_id = "pp handler level 3."
        return res

    def get_properties(self):

        if self.level == "1":
            res = self.get_properties_generic_level1()
        elif self.level == "2":
            res = self.get_properties_pp_level2()
        elif self.level == "3":
            res = self.get_properties_pp_level3()

        res["info"]["format"] = self.FILE_FORMAT

        return res

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass
