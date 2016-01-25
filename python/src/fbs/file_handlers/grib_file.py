import gribapi as gapi
import fbs_lib.util as util

from fbs.file_handlers.generic_file import GenericFile

class GribFile(GenericFile):
    """
    Class for returning basic information about the content
    of an Grib file.
    """

    def __init__(self, file_path, level, additional_param=None):
        GenericFile.__init__(self, file_path, level)
        self.FILE_FORMAT = "GRIB"

    def get_handler_id(self):
        return self.handler_id

    def phenomena_level2(self):

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
                      "name"
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
                    if len(key) < util.NETCDF_MAX_PAR_LENGTH \
                       and len(value) < util.NETCDF_MAX_PAR_LENGTH:

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
            grib_phenomena = self.phenomena_level2()

            self.handler_id = "grib handler level 2."

            if grib_phenomena is None:
                return file_info

            file_info["phenomena"] = grib_phenomena

            return file_info

        else:
            return None



    def phenomena_level3(self):

        """
        Construct list of Phenomena based on variables in Grib file.
        :returns : List of phenomena.
        """
        phenomenon_attr = {}
        phenomena_list = []
        phenomenon_parameters_dict = {}
        lat_f = None
        lon_f = None
        lat_l = None
        lon_l = None
        date_d = None
        date_t = None

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
                      "longitudeOfLastGridPointInDegrees",
                      "dataDate",
                      "dataTime"
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
                        lat_f = None
                        lon_f = None
                        lat_l = None
                        lon_l = None
                        date_d = None
                        date_t = None
                        break

                    value = str(gapi.grib_get(gid, key))

                    #So the file contains many records but all report the
                    #same spatial and temporal information. Only complete distinct records 
                    #will be stored i.e the one that contain the full list of parameter
                    #and are unique. If evety record has got different spatial and temporal
                    #then th eindex must change because currently there is only on geo_shape_field.
                    if key == "latitudeOfFirstGridPointInDegrees" and lat_f is None:
                        lat_f = value
                    elif key == "longitudeOfFirstGridPointInDegrees" and lon_f is None:
                        lon_f = value
                    elif key == "latitudeOfLastGridPointInDegrees" and lat_l is None:
                        lat_l = value
                    elif key =="longitudeOfLastGridPointInDegrees" and lon_l is None:
                        lon_l = value
                    elif key == "dataDate" and date_d is None:
                        date_d = value
                    elif key == "dataTime" and date_t is None:
                        date_t = value
                    else:
                        if len(key) < util.NETCDF_MAX_PAR_LENGTH \
                           and len(value) < util.NETCDF_MAX_PAR_LENGTH:

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
            #ok, if there are temporal and geospatial data these can be added.
            #based on the assaumption that there is onl;y one record of this 
            #in the whole file. 
            phen_geo_tem_data = {}
            geospatial_dict = {}
            temporal_dict = {}
            if lat_f is not None      \
               and lon_f is not None  \
               and lat_l is not None  \
               and lon_l is not None  \
               and date_d is not None \
               and date_t is not None:

                geospatial_dict["type"] = "envelope"
                if float(lon_l) > 180:
                    lon_l = (float(lon_l) -180) - 180
                geospatial_dict["coordinates"] = [[lat_f, lon_f], [lat_l, lon_l]]

                temporal_dict["start_time"] = date_d
                temporal_dict["end_time"] = date_t


            phen_geo_tem_data["phen_data"] = phenomena_list
            phen_geo_tem_data["geo_data"] = geospatial_dict
            phen_geo_tem_data["tmp_data"] = temporal_dict

            return phen_geo_tem_data

        except Exception:
            return None

    def get_properties_grib_level3(self):
        """
        Wrapper for method phenomena().
        :returns:  A dict containing information compatible with current es index level 2.
        """

        file_info = self.get_properties_generic_level1()

        if file_info is not None:

            #level 2.
            grib_phenomena = self.phenomena_level3()

            self.handler_id = "grib handler level 3."

            if grib_phenomena is None:
                return file_info

            file_info["phenomena"] = grib_phenomena["phen_data"]
            loc_dict = {}
            loc_dict["coordinates"] = grib_phenomena["geo_data"]
            file_info["spatial"] = loc_dict

            file_info["temporal"] = grib_phenomena["tmp_data"]

            return file_info

        else:
            return None

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
