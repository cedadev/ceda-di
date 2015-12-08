import gribapi as gapi
import ceda_fbs.util.util as util

from ceda_fbs.file_handlers.generic_file import GenericFile

class GribFile(GenericFile):
    """
    Class for returning basic information about the content
    of an Grib file.
    """

    def __init__(self, file_path, level):
        GenericFile.__init__(self, file_path, level)
        self.FILE_FORMAT = "GRIB"

    def get_handler_id(self):
        return self.handler_id

    def phenomena(self):

        """
        Construct list of Phenomena based on variables in Grib file.
        :returns : List of phenomena.
        """
        phenomenon_attr = {}
        phenomena_list = []
        phenomenon_parameters_dict = {}

        phen_keys = [
                      "paramId",
                      "cfNameECMF",
                      "cfName",
                      "cfVarName",
                      "units",
                      "nameECMF",
                      "name",
                      "Ni",
                      "Nj",
                      "latitudeOfFirstGridPointInDegrees",
                      "longitudeOfFirstGridPointInDegrees",
                      "latitudeOfLastGridPointInDegrees",
                      "longitudeOfLastGridPointInDegrees"
                    ]
        try:
            fd = open(self.file_path)

            found = set()

            while 1:
                gid = gapi.grib_new_from_file(fd)
                if gid is None: break

                list_of_phenomenon_parameters = []
                list_of_phenomenon_parameters_t = []

                for key in phen_keys:

                    if not gapi.grib_is_defined(gid, key):
                        break

                    value = str(gapi.grib_get(gid, key))
                    if len(key) < util.NETCDF_MAX_PHEN_LENGTH \
                       and len(value) < util.NETCDF_MAX_PHEN_LENGTH:

                        phenomenon_attr["name"] = key
                        phenomenon_attr["value"] = value

                        list_of_phenomenon_parameters.append(phenomenon_attr.copy())
                        list_of_phenomenon_parameters_t.append((key, value))

                """
                phenomenon_attr["name"] = "var_id"
                phenomenon_attr["value"] = "None"
                list_of_phenomenon_parameters.append(phenomenon_attr.copy())
                phenomenon_attr.clear()
                list_of_phenomenon_parameters_t.append(("name", "None"))
                """
                list_of_phenomenon_parameters_tt = tuple(list_of_phenomenon_parameters_t)

                if list_of_phenomenon_parameters_tt not in found:
                    found.add(list_of_phenomenon_parameters_tt)
                    #Dict of phenomenon attributes.
                    phenomenon_parameters_dict["phenomenon_parameters"] = list_of_phenomenon_parameters

                    #list of phenomenon.
                    phenomena_list.append(phenomenon_parameters_dict.copy())
                    phenomenon_parameters_dict.clear()
                else:
                    phenomenon_parameters_dict.clear()

                gapi.grib_release(gid)

            fd.close()
            """
            phenomena_list_unique = []
            for item in phenomena_list:
                if item not in phenomena_list_unique:
                    phenomena_list_unique.append(item)
            """
            return phenomena_list

        except Exception:
            return None

    def get_properties_grib_level2(self):
        """
        Wrapper for method phenomena().
        :returns:  A dict containing information compatible with current es index level 2.
        """

        file_info = self.get_properties_generic_level1()

        if file_info is not None:

            #level 2.
            grib_phenomena = self.phenomena()

            self.handler_id = "grib handler level 2."

            if grib_phenomena is None:
                return file_info

            file_info["phenomena"] = grib_phenomena

            return file_info

        else:
            return None

    def get_properties_grib_level3(self):
        res = self.get_properties_grib_level2()
        self.handler_id = "grib handler level 3."
        return res

    def get_properties(self):

        if self.level == "1":
            res = self.get_properties_generic_level1()
        elif self.level == "2":
            res = self.get_properties_grib_level2()
        elif self.level == "3":
            res = self.get_properties_grib_level3()

        #Sice file format is decided it can be added. 
        res["info"]["format"] = self.FILE_FORMAT

        return res

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass
