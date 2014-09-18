"""
Test module for eufar.exif_geo
"""

import unittest

from eufar.exif_geo import EXIF

class TestEXIF(unittest.TestCase):
    """Test class for eufar.exif_geo.EXIF"""
    def setUp(self):
        self.path = "/path/to/some/file"
        self.xml = {
            "Camera_Image": {
                "Plane_info": {
                    "Exterior_orientation": {
                        "Position": {
                            "Latitude": 1.234,
                            "Longitude": 4.321,
                            "Height": 9.876
                        }
                    }
                },
                "Project_info": {
                    "Year": 1901,
                    "Flight_day_of_year": 5,
                    "GPStime_of_week": 86401
                }
            }
        }


    def test_get_geospatial(self):
        with EXIF(self.path) as exif_file:
            exif_file.xml = self.xml
            assert exif_file.get_geospatial() == {
                "lat": [1.234],
                "lon": [4.321],
                "alt": [9.876]
            }

            exif_file.xml = {}
            self.assertRaises(KeyError, exif_file.get_temporal)

    def test_get_temporal(self):
        with EXIF(self.path) as exif_file:
            exif_file.xml = self.xml
            time_dict = exif_file.get_temporal()
            assert time_dict["start_time"] == "1901-01-05T00:00:01"
            assert time_dict["end_time"] == time_dict["start_time"]

            exif_file.xml = {}
            self.assertRaises(KeyError, exif_file.get_temporal)
