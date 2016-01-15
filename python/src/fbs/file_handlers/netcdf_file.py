import netCDF4


from fbs.file_handlers.generic_file import GenericFile
import fbs_lib.util as util
import fbs_lib.geojson as geojson

class   NetCdfFile(GenericFile):
    """
    Simple class for returning basic information about the content
    of an NetCDF file.
    """

    def __init__(self, file_path, level, additional_param=None):
        GenericFile.__init__(self, file_path, level)
        self.FILE_FORMAT = "NetCDF"

    def get_handler_id(self):
        return self.handler_id

    def clean_coordinate(self, coord):
        """Return True if coordinate is valid."""
        try:
            # This filters out misconfigured "_FillValue" elements
            if coord == 0.0:
                return False

            int(coord)  # If this fails, "coord" is not a number!

            return True
        except ValueError:
            return False


    def geospatial(self, ncdf, lat_name, lon_name):
        """
        Return a dict containing lat/lons from NetCDF file.

        :param Dataset ncdf: Reference to an opened netcdf4.Dataset object
        :param lat_name: Name of parameter containing latitude values
        :param lon_name: Name of parameter containing longitude values
        :returns: Geospatial information as dict.
        """

        # Filter out items that are equal to "masked"
        lats = filter(self.clean_coordinate,
                      ncdf.variables[lat_name][:].ravel())
        lons = filter(self.clean_coordinate,
                      ncdf.variables[lon_name][:].ravel())
        return {
            "type": "track",
            "lat": lats,
            "lon": lons
        }


    def find_var_by_standard_name(self, ncdf, fpath, standard_name):
        """
        Find a variable reference searching by CF standard name.

        :param Dataset ncdf: Reference to an opened netCDF4.Dataset object
        :param str standard_name: The CF standard name to search for
        """
        for key, value in ncdf.variables.iteritems():
            try:
                if value.standard_name.lower() == standard_name.lower():
                    return key
            except AttributeError:
                continue

        return None

    #ok lets try something new.
    def get_geospatial(self, ncdf):
        lat_name = self.find_var_by_standard_name(ncdf, self.file_path, "latitude")
        lon_name = self.find_var_by_standard_name(ncdf, self.file_path, "longitude")

        if lat_name and lon_name:
            return self.geospatial(ncdf, lat_name, lon_name)
        else:
            return None

    def temporal(self, ncdf, time_name):
        """
        Extract time values from Dataset using the variable name provided.

        :param Dataset ncdf: Reference to an opened netcdf4.Dataset object
        :param str time_name: Name of the time parameter
        """
        times = list(netCDF4.num2date(list(ncdf.variables[time_name]),
                                      ncdf.variables[time_name].units))
        return {
            "start_time": times[0].isoformat(),
            "end_time": times[-1].isoformat()
        }

    def get_temporal(self, ncdf):
        time_name = self.find_var_by_standard_name(ncdf, self.file_path, "time")
        return self.temporal(ncdf, time_name) 

    def is_valid_parameter(self, item):
        valid_parameters = [ "standard_name",
                             "long_name",
                             "title",
                             "name",
                             "units"
                           ]
        if item["name"] in valid_parameters \
           and len(item["value"]) < util.NETCDF_MAX_PAR_LENGTH\
           and len(item["name"]) < util.NETCDF_MAX_PAR_LENGTH:
            return True
        return False

    def phenomena(self, netcdf):
        """
        Construct list of Phenomena based on variables in NetCDF file.
        :returns : List of metadata.product.Parameter objects.
        """
        phens_list = []
        #for all phenomena list.
        for v_name, v_data in netcdf.variables.iteritems():
            phen_par_list = []
            #for all attributtes in phenomenon.
            for key, value in v_data.__dict__.iteritems():
                phen_par = { "name" : key.strip(),
                             "value": unicode(value).strip()
                           }

                if self.is_valid_parameter(phen_par):
                    phen_par_list.append(phen_par.copy())

            phen_par = { "name" : "var_id",
                          "value" : v_name
                       }
            phen_par_list.append(phen_par.copy())

            phens_list.append(phen_par_list)

        return phens_list

    def get_properties_netcdf_file_level2(self, netcdf, index):
        """
        Wrapper for method phenomena().
        :returns:  A dict containing information compatible with current es index level 2.
        """
        #Get basic file info.

        self.handler_id = "Netcdf handler level 2."

        netcdf_phenomena = self.phenomena(netcdf)

        phenomena_list = []
        phenomenon_parameters_dict = {}

        for phenomenon_par in netcdf_phenomena:
            phenomenon_parameters_dict["phenomenon_parameters"] = phenomenon_par
            phenomena_list.append(phenomenon_parameters_dict.copy())
            phenomenon_parameters_dict.clear()


        index["phenomena"] = phenomena_list


        return index

    def get_properties_netcdf_level2(self):

        #level 1.
        file_info = self.get_properties_generic_level1()

        if file_info is not None:

            #ok basic info exist, lets add level 2 info.
            try:
                with netCDF4.Dataset(self.file_path) as netcdf_object:
                    level2_meta = self.get_properties_netcdf_file_level2(netcdf_object, file_info)
                    return level2_meta
            #Catch all possible errors that can be related to this file and and record the error later.   
            except Exception:
                return file_info
        else:
            return None

    def get_properties_netcdf_level3(self):

        """
        Wrapper for method phenomena().
        :returns:  A dict containing information compatible with current es index level 2.
        """
        #level 1
        file_info = self.get_properties_generic_level1()

        if file_info is not None:

            try:
                with netCDF4.Dataset(self.file_path) as netcdf:

                    #level 2
                    level2_meta = self.get_properties_netcdf_file_level2(netcdf, file_info)

                    self.handler_id = "Netcdf handler level 3."

                    #try to add level 3 info. 
                    try:
                        geo_info = self.get_geospatial(netcdf)

                        loc_dict= {}

                        gj = geojson.GeoJSONGenerator(geo_info["lat"], geo_info["lon"])
                        spatial = gj.get_elasticsearch_geojson()

                        loc_dict["coordinates"]= spatial["geometries"]["search"]#["coordinates"]
                        level2_meta["spatial"] = loc_dict
                    except AttributeError:
                        pass

                    try:
                        temp_info = self.get_temporal(netcdf)
                        level2_meta["temporal"] = temp_info
                    except AttributeError:
                        pass

                    return level2_meta
            except Exception as ex:
                print ex
                return file_info
        else:
            return None

    def get_properties(self):

        if self.level == "1":
            res = self.get_properties_generic_level1()
        elif self.level == "2":
            res = self.get_properties_netcdf_level2()
        elif self.level == "3":
            res = self.get_properties_netcdf_level3()

        res["info"]["format"] = self.FILE_FORMAT

        return res

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass