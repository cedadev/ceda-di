"""
Test module for ceda_di.metadata.product
"""

import unittest
from hamcrest import *
import numpy.ma as ma

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


class TestGeoJSONGenerator(unittest.TestCase):

    def assert_type_and_coords(self, actual, is_polygon, lat_bottom, lat_top, lon_left, lon_right):

        if is_polygon:
            assert_that(actual["type"], is_("polygon"), "bbounding box type")
            bounds = [[[lon_right, lat_top], [lon_left, lat_top], [lon_left, lat_bottom], [lon_right, lat_bottom], [lon_right, lat_top]]]
            assert_that(actual["coordinates"], is_(bounds), "bbounding box type")

        else:
            assert_that(actual["type"], is_("envelope"), "bbounding box type")
            bounds = [[lon_left, lat_top], [lon_right, lat_bottom]]
            assert_that(actual["coordinates"], is_(bounds), "bbounding box type")

    def test_GIVEN_no_entries_THEN_bounding_box_is_empty(self):
        gen = GeoJSONGenerator(latitudes=[], longitudes=[])

        box = gen._gen_bbox()

        assert_that(box, is_(None), "bbox should be none")

    def test_GIVEN_one_entry_THEN_bounding_box_is_that_entry(self):
        gen = GeoJSONGenerator(latitudes=[1.0], longitudes=[2.0])

        box = gen._gen_bbox()

        self.assert_type_and_coords(box, True, 1.0, 1.0, 2.0, 2.0)

    def test_GIVEN_one_entry_for_envelope_THEN_bounding_box_is_that_entry(self):
        gen = GeoJSONGenerator(latitudes=[1.0], longitudes=[2.0])

        box = gen._gen_envelope()

        self.assert_type_and_coords(box, False, 1.0, 1.0, 2.0, 2.0)

    def test_GIVEN_two_entry_for_envelope_THEN_bounding_box_is_that_entry(self):
        gen = GeoJSONGenerator(latitudes=[1.0, 3.0], longitudes=[2.0, 5.0])

        box = gen._gen_envelope()

        self.assert_type_and_coords(box, False, 1.0, 3.0, 2.0, 5.0)

    def test_GIVEN_two_entry_for_envelope_with_lats_and_lons_in_reverse_order_THEN_bounding_box_is_lons_in_same_order_lats_in_other_order(self):
        gen = GeoJSONGenerator(latitudes=[3.0, 1.0], longitudes=[5.0, 2.0])

        box = gen._gen_envelope()

        self.assert_type_and_coords(box, False, 1.0, 3.0, 5.0, 2.0)

    def test_GIVEN_three_entry_for_envelope_with_lats_and_lons_in_any_order_on_front_of_globe_THEN_bounding_box_is_min_to_max(self):
        gen = GeoJSONGenerator(latitudes=[3.1, 5.1, 1.1], longitudes=[5.0, 1.0,  2.0])

        box = gen._gen_envelope()

        self.assert_type_and_coords(box, False, 1.1, 5.1, 1.0, 5.0)

    def test_GIVEN_three_entry_for_envelope_with_lats_and_lons_in_any_order_on_back_of_globe_THEN_bounding_box_is_min_to_max(self):
        gen = GeoJSONGenerator(latitudes=[3.1, 5.1, 1.1], longitudes=[-160, -170,  170])

        box = gen._gen_envelope()

        self.assert_type_and_coords(box, False, 1.1, 5.1, 170, -160)

    def test_GIVEN_three_equispaced_entries_for_envelope_with_lats_and_lons_in_any_order_on_back_of_globe_THEN_bounding_box_is_on_front_of_globe(self):
        gen = GeoJSONGenerator(latitudes=[3.1, 5.1, 1.1], longitudes=[0, 120,  -120])

        box = gen._gen_envelope()

        self.assert_type_and_coords(box, False, 1.1, 5.1, -120, 120)

    def test_GIVEN_masked_entries_for_lats_and_lons_in_any_order_on_back_of_globe_THEN_masked_enties_ignored(self):
        latitudes = ma.masked_array([3.1, 5.1, 1.1], [False, True, False])
        longitudes = ma.masked_array([0, 120,  -120], [False, False, True])
        gen = GeoJSONGenerator(latitudes=latitudes, longitudes=longitudes)

        box = gen._gen_envelope()

        # @charlienewey: Changed this test because masked entries are now not
        # used in generating bounding boxes
        # self.assert_type_and_coords(box, False, 1.1, 3.1, 0, 120)
        self.assert_type_and_coords(box, False, 3.1, 3.1, 0, 0)

    def test_GIVEN_masked_entries_for_lats_and_lons_THEN_summary_does_not_contain_elements(self):
        latitudes = ma.masked_array([3, 5.1, 1.1, 6.5], [False, True, False, False])
        longitudes = ma.masked_array([0, 120,  -120, 100], [False, False, True, False])
        gen = GeoJSONGenerator(latitudes=latitudes, longitudes=longitudes)

        geojson = gen.get_elasticsearch_geojson()

        for result, expected in zip(geojson["geometries"]["display"]["coordinates"], [(0, 3.0), (100, 6.5)]):
            assert_that(result[0], close_to(expected[0], 0.01), "lat" )
            assert_that(result[1], close_to(expected[1], 0.01), "lon")

    def test_GIVEN_more_than_one_entry_and_no_type_THEN_geojson_is_track_type(self):
        latitudes = [3, 5, 1, 6]
        longitudes = [0, 120,  -120, 100]

        gen = GeoJSONGenerator(latitudes, longitudes)
        geojson = gen.get_elasticsearch_geojson()
        expected_geojson = {
            "geometries": {
                "search": {
                    "type": "LineString",
                    "coordinates": [
                        (0, 3),
                        (120, 5),
                        (-120, 1),
                        (100, 6)
                    ]
                },
                "display": {
                    "type": "LineString",
                    "coordinates": [
                        (0, 3),
                        (120, 5),
                        (-120, 1),
                        (100, 6)
                    ]
                }
            }
        }

        assert_that(geojson, is_(expected_geojson))

    def test_GIVEN_coordinates_with_point_type_THEN_geojson_is_point_type(self):
        latitudes = [3, 5, 1, 6]
        longitudes = [0, 120,  -120, 100]

        gen = GeoJSONGenerator(latitudes, longitudes, shape_type="point")
        geojson = gen.get_elasticsearch_geojson()

        # Remember that if a "point" type annotation is supplied, then it's
        # only the first pair of coordinates that are used.
        expected_geojson = {
            "geometries": {
                "search": {
                    "type": "Point",
                    "coordinates": [0, 3]
                },
                "display": {
                    "type": "Point",
                    "coordinates": [0, 3]
                }
            }
        }

        assert_that(geojson, is_(expected_geojson))

    def test_GIVEN_coordinates_with_swath_type_THEN_geojson_is_swath_type(self):
        # This is a little hard to test without the codelooking horrific,
        # so you'll have to take my word for it that this is supposed to
        # generate three bounding boxes that cross Ireland.
        #
        # You can go to "http://geojsonlint.com" and paste in the GeoJSON in
        # "expected_search_geojson" to verify.
        longitudes = [
            -10.854492, -9.711914, -7.734375, -5.537109
        ]

        latitudes = [
            49.037868, 52.106505, 54.622978, 56.632064
        ]

        gen = GeoJSONGenerator(latitudes, longitudes, shape_type="swath")
        geojson = gen.get_elasticsearch_geojson()
        expected_search_geojson = {
            "type": "MultiPolygon",
            "coordinates": [
                [
                    [
                        [-9.711914, 52.106505],
                        [-10.854492, 52.106505],
                        [-10.854492, 49.037868],
                        [-9.711914, 49.037868],
                        [-9.711914, 52.106505]
                    ]
                ],
                [
                    [
                        [-7.734375, 54.622978],
                        [-9.711914, 54.622978],
                        [-9.711914, 52.106505],
                        [-7.734375, 52.106505],
                        [-7.734375, 54.622978]
                    ]
                ],
                [
                    [
                        [-5.537109, 56.632064],
                        [-7.734375, 56.632064],
                        [-7.734375, 54.622978],
                        [-5.537109, 54.622978],
                        [-5.537109, 56.632064]
                    ]
                ]
            ]
        }

        expected_display_geojson = {
            "type": "LineString",
            "coordinates": zip(longitudes, latitudes)
        }

        assert_that(geojson["geometries"]["search"], is_(expected_search_geojson))
        assert_that(geojson["geometries"]["display"], is_(expected_display_geojson))

    def test_GIVEN_coordinates_with_track_type_THEN_geojson_is_track_type(self):
        latitudes = [3, 5, 1, 6]
        longitudes = [0, 120,  -120, 100]

        gen = GeoJSONGenerator(latitudes, longitudes, shape_type="track")
        geojson = gen.get_elasticsearch_geojson()
        expected_geojson = {
            "geometries": {
                "search": {
                    "type": "LineString",
                    "coordinates": [
                        (0, 3),
                        (120, 5),
                        (-120, 1),
                        (100, 6)
                    ]
                },
                "display": {
                    "type": "LineString",
                    "coordinates": [
                        (0, 3),
                        (120, 5),
                        (-120, 1),
                        (100, 6)
                    ]
                }
            }
        }

    def test_GIVEN_two_differently_sized_coordinate_lists_THEN_num_points_returns_correct_value(self):
        latitudes = [3, 5, 1]  # shorter list
        longitudes = [0, 120,  -120, 100]

        gen = GeoJSONGenerator(latitudes, longitudes)
        assert_that(gen._num_points(longitudes, latitudes), is_(3))
