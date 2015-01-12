"""
Test module for ceda_di.metadata.product
"""

import unittest
from hamcrest import *

from ceda_di.metadata.product import Properties, Parameter, GeoJSONGenerator


class TestProperties(unittest.TestCase):
    def setUp(self):
        # Just some dummy data (totally arbitrary)
        fs = {"size": 3, "path": "/some/non/existent/path", "filename":"filename"}
        tmp = {"start_time": "2014-09-22T20:51:53Z",
               "end_time": "2014-09-22T20:51:53Z"}
        df = {"data_format": "spam"}
        self.lat_bottom = -54.93456077
        self.lat_top = 36.8623985
        self.lon_left = -170.2979817
        self.lon_right = -69.18607194
        sp = {"lat": [self.lat_top, 36.8623985, self.lat_bottom],
              "lon": [-130.75576671, self.lon_left , self.lon_right]}
        par = [Parameter("test"), Parameter("spam")]

        self.prop = Properties(filesystem=fs, spatial=sp, temporal=tmp,
                               data_format=df, parameters=par, test="foo")

    def test_gen_bbox(self):
        bbox = self.prop.spatial["geometries"]["bbox"]
        assert_that(bbox["type"], "polygon", "bbox type")
        bounds = [[self.lon_right, self.lat_top], [self.lon_left, self.lat_top], [self.lon_left, self.lat_bottom], [self.lon_right, self.lat_bottom]]
        assert_that(bbox["coordinates"], bounds, "bbox type")

class TestGeoJSONGenerator(unittest.TestCase):

    def assert_type_and_coords(self, actual, is_polygon, lat_bottom, lat_top, lon_left, lon_right):

        if is_polygon:
            assert_that(actual["type"], is_("polygon"), "bbounding box type")
            bounds = [[lon_right, lat_top], [lon_left, lat_top], [lon_left, lat_bottom], [lon_right, lat_bottom]]
            assert_that(actual["coordinates"], is_(bounds), "bbounding box type")

        else:
            assert_that(actual["type"], is_("envelope"), "bbounding box type")
            bounds = [[lon_left, lat_top], [lon_right, lat_bottom]]
            assert_that(actual["coordinates"], is_(bounds), "bbounding box type")


    def test_valid_lat(self):
        # Lovely lovely edge cases
        lats = [90, -90, 0, -91, 91]
        assert filter(GeoJSONGenerator.valid_lat, lats) == [90, -90, 0]

    def test_valid_lon(self):
        # More lovely edge cases
        lons = [180, -180, 0, -181, 181]
        assert filter(GeoJSONGenerator.valid_lon, lons) == [180, -180, 0]

    def test_GIVEN_no_entries_THEN_bounding_box_is_empty(self):
        gen = GeoJSONGenerator(latitudes=[], longitudes=[])

        box = gen.generate_bounding_box(True)

        assert_that(box, is_(None), "bbox should be none")

    def test_GIVEN_one_entry_THEN_bounding_box_is_that_entry(self):
        gen = GeoJSONGenerator(latitudes=[1.0], longitudes=[2.0])

        box = gen.generate_bounding_box(True)

        self.assert_type_and_coords(box, True, 1.0, 1.0, 2.0, 2.0)

    def test_GIVEN_one_entry_for_envelope_THEN_bounding_box_is_that_entry(self):
        gen = GeoJSONGenerator(latitudes=[1.0], longitudes=[2.0])

        box = gen.generate_bounding_box(False)

        self.assert_type_and_coords(box, False, 1.0, 1.0, 2.0, 2.0)

    def test_GIVEN_two_entry_for_envelope_THEN_bounding_box_is_that_entry(self):
        gen = GeoJSONGenerator(latitudes=[1.0, 3.0], longitudes=[2.0, 5.0])

        box = gen.generate_bounding_box(False)

        self.assert_type_and_coords(box, False, 1.0, 3.0, 2.0, 5.0)

    def test_GIVEN_two_entry_for_envelope_with_lats_and_lons_in_reverse_order_THEN_bounding_box_is_lons_in_same_order_lats_in_other_order(self):
        gen = GeoJSONGenerator(latitudes=[3.0, 1.0], longitudes=[5.0, 2.0])

        box = gen.generate_bounding_box(False)

        self.assert_type_and_coords(box, False, 1.0, 3.0, 5.0, 2.0)

    def test_GIVEN_three_entry_for_envelope_with_lats_and_lons_in_any_order_on_front_of_globe_THEN_bounding_box_is_min_to_max(self):
        gen = GeoJSONGenerator(latitudes=[3.1, 5.1, 1.1], longitudes=[5.0, 1.0,  2.0])

        box = gen.generate_bounding_box(False)

        self.assert_type_and_coords(box, False, 1.1, 5.1, 1.0, 5.0)

    def test_GIVEN_three_entry_for_envelope_with_lats_and_lons_in_any_order_on_back_of_globe_THEN_bounding_box_is_min_to_max(self):
        gen = GeoJSONGenerator(latitudes=[3.1, 5.1, 1.1], longitudes=[-160, -170,  170])

        box = gen.generate_bounding_box(False)

        self.assert_type_and_coords(box, False, 1.1, 5.1, 170, -160)

    def test_GIVEN_three_equispaced_entries_for_envelope_with_lats_and_lons_in_any_order_on_back_of_globe_THEN_bounding_box_is_on_front_of_globe(self):
        gen = GeoJSONGenerator(latitudes=[3.1, 5.1, 1.1], longitudes=[0, 120,  -120])

        box = gen.generate_bounding_box(False)

        self.assert_type_and_coords(box, False, 1.1, 5.1, -120, 120)
