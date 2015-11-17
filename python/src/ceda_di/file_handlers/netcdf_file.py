import netCDF4


from ceda_di.file_handlers.generic_file import GenericFile
from ceda_di.metadata import product
from ceda_di.metadata.product import GeoJSONGenerator

class   NetCdfFile(GenericFile):
    """
    Simple class for returning basic information about the content
    of an NetCDF file.
    """

    def __init__(self, file_path, level):
        GenericFile.__init__(self, file_path, level)

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

    def phenomena(self, netcdf):
        """
        Construct list of Phenomena based on variables in NetCDF file.
        :returns : List of metadata.product.Parameter objects.
        """
        phens = []
        for v_name, v_data in netcdf.variables.iteritems():
            phen = product.Parameter(v_name, v_data.__dict__)
            phens.append(phen)

        return phens

    def get_properties_netcdf_file_level2(self, netcdf):
        """
        Wrapper for method phenomena().
        :returns:  A dict containing information compatible with current es index level 2.
        """
        #Get basic file info.
        file_info = self.get_properties_generic_level1()

        if file_info is not None:

            self.handler_id = "Netcdf handler level 2."

            netcdf_phenomena = self.phenomena(netcdf)
                        
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
            return None

    def get_properties_netcdf_level2(self):

        try:
            with netCDF4.Dataset(self.file_path) as netcdf_object:
                level2_meta = self.get_properties_netcdf_file_level2(netcdf_object)
                return level2_meta
        #Catch all possible errors that can be related to this file and and record the error later.   
        except Exception:
            return self.get_properties_generic_level2()

    def get_properties_netcdf_level3(self):

        """
        Wrapper for method phenomena().
        :returns:  A dict containing information compatible with current es index level 2.
        """

        try:
            with netCDF4.Dataset(self.file_path) as netcdf:

                level2_meta = self.get_properties_netcdf_file_level2(netcdf)

                #just in case.
                if level2_meta == None:
                    return None

                self.handler_id = "Netcdf handler level 3."

                #try to add level 3 info. 
                try:
                    geo_info = self.get_geospatial(netcdf)

                    loc_dict= {}

                    gj = GeoJSONGenerator(geo_info["lat"], geo_info["lon"])
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
        except Exception:
            return None

    def get_properties(self):

        if self.level == "1":
            return self.get_properties_generic_level1()
        elif self.level == "2":
            return self.get_properties_netcdf_level2()
        elif self.level == "3":
            return self.get_properties_netcdf_level3()


    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass