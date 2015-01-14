from unittest import TestCase
import simplejson as json
import os
import sys
import datetime as dt
from hamcrest import assert_that, is_, close_to

from ceda_di.main import Main


class TestCloudSat(TestCase):
    """
    Test that CEDA DI can read CloudSat data:
    """

    CONFIG_FILE = '../../../config/ceda_di.json'
    TEST_DIR = 'test_files'
    CLOUD_SAT_FILE = os.path.join(TEST_DIR, '2007189224156_06358_CS_2C-PRECIP-COLUMN_GRANULE_P_R04_E02.hdf')
    JSON_FILE = os.path.join(TEST_DIR, 'json/2007189224156_06358_CS_2C-PRECIP-COLUMN_GRANULE_P_R04_E02.json')

    @classmethod
    def setUpClass(cls):
        # Process the file in the class setup method so it only has to do the slow bit once for all tests.
        sys.argv[1] = cls.CONFIG_FILE
        main = Main()
        main.conf['outputpath'] = main.outpath = cls.TEST_DIR
        main.conf['jsonpath'] = main.jsonpath = cls.TEST_DIR + '/json'
        main.process_file(cls.CLOUD_SAT_FILE)

    def get_output_json(self):
        fp = open(self.JSON_FILE)
        return json.load(fp)

    def test_json_has_start_time(self):
        json_body = self.get_output_json()
        start_date_str = json_body['temporal']['start_time']
        start_date = dt.datetime.strptime(start_date_str, "%Y-%m-%dT%H:%M:%S.%f")
        assert_that(start_date, is_(dt.datetime(2007, 7, 8, 22, 42, 1, 999987)))

    def test_json_has_end_time(self):
        json_body = self.get_output_json()
        end_date_str = json_body['temporal']['end_time']
        end_date = dt.datetime.strptime(end_date_str, "%Y-%m-%dT%H:%M:%S.%f")
        assert_that(end_date, is_(dt.datetime(2007, 7, 9, 0, 20, 54, 999992)))

    def test_json_has_geo_bounds(self):
        json_body = self.get_output_json()
        geo_bbox = json_body['spatial']['geometries']['bbox']
        lat_bounds = geo_bbox['coordinates']
        lat_min, lat_max = -81.851, 81.851
        lon_min, lon_max = -179.992, 179.992
        bottom_left = lat_bounds[0]
        bottom_right = lat_bounds[3]
        top_left = lat_bounds[1]
        top_right = lat_bounds[2]

        def compare_array(array1, array2):
            for i in range(len(array1)):
                assert_that(array1[i], close_to(array2[i], 0.01))

        compare_array(bottom_left, [lon_min, lat_min])
        compare_array(bottom_right, [lon_max, lat_min])
        compare_array(top_left, [lon_min, lat_max])
        compare_array(top_right, [lon_max, lat_max])

    def test_json_has_parameters(self):
        json_body = self.get_output_json()
        parameters = json_body['parameters']
        assert_that(len(parameters), is_(37))


        def get_variable_attribute_value_by_name(variable_attributes, attribute_name):
            """
            Get the value of a specified variable attribute from a list of attribute dictionaries,
            each containing a 'name' and 'value' key.

            :param variable_attributes: List of variable attribute dictionaries of format
            {"name": name, "value": value}
            :returns: value of matching attribute
            """
            for attribute in variable_attributes:
                if attribute['name'] == attribute_name:
                    return attribute['value']

        for variable_attrs in parameters:
            long_name = get_variable_attribute_value_by_name(variable_attrs, 'long_name')
            # Chosen one parameter to test
            if long_name == 'Digital Elevation Map':
                assert_that(len(variable_attrs), is_(12))
                standard_name = get_variable_attribute_value_by_name(variable_attrs, 'standard_name')
                shape = get_variable_attribute_value_by_name(variable_attrs, 'shape')
                factor = get_variable_attribute_value_by_name(variable_attrs, 'factor')
                units = get_variable_attribute_value_by_name(variable_attrs, 'units')
                calendar = get_variable_attribute_value_by_name(variable_attrs, 'calendar')
                missing_value = get_variable_attribute_value_by_name(variable_attrs, 'missing_value')
                history = get_variable_attribute_value_by_name(variable_attrs, 'history')
                _range = get_variable_attribute_value_by_name(variable_attrs, 'range')
                offset = get_variable_attribute_value_by_name(variable_attrs, 'offset')

                assert_that(standard_name, is_('DEM_elevation'))
                assert_that(shape, is_('[37082]'))
                assert_that(factor, is_('1.0'))
                assert_that(units, is_('meters'))
                assert_that(calendar, is_(''))
                assert_that(missing_value, is_('9999'))
                assert_that(history, is_(''))
                assert_that(_range, is_('[-9999, 8850]'))
                assert_that(offset, is_('0.0'))
                return

        # If we got here it means that we couldn't find a matching parameter so we should fail
        raise AssertionError("Digital Elevation Model not found in list of parameters")

