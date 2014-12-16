from unittest import TestCase
from ceda_di.extract import HandlerFactory


class TestHandlerFactory(TestCase):
    """
    Tests that the HandlerFactory can correctly identify the handler
    to instantiate given a filename.
    """

    def setUp(self):
        handler_map = {
            "_nav_post_processed.bil.hdr$": {
                "class": "ceda_di.envi_geo.BIL",
                "priority": 10
            },
            ".hdf$": {
                "class": "ceda_di.hdf4_geo.HDF4",
                "priority": 10
            },
            ".tif$": {
                "class": "ceda_di.exif_geo.EXIF",
                "priority": 10
            },
            ".nc$": {
                "class": "ceda_di.netcdf_geo.NetCDFFactory",
                "priority": 1
            },
            ".*_CS_.*GRANULE.*\\.hdf$": {
                "class": "ceda_di.jascis.CloudSat",
                "priority": 1
            },
        }
        self.handler_factory = HandlerFactory(handler_map)

    def test_GIVEN_bil_filename_WHEN_get_file_handler_class_THEN_bil_handler_returned(self):
        filename = 'test_nav_post_processed.bil.hdr'
        handler = self.handler_factory.get_handler_class(filename)
        assert handler.__name__ == "BIL"

    def test_GIVEN_exif_filename_WHEN_get_file_handler_class_THEN_exif_handler_returned(self):
        filename = 'exif_file_test_name.tif'
        handler = self.handler_factory.get_handler_class(filename)
        assert handler.__name__ == "EXIF"

    def test_GIVEN_hdf_filename_WHEN_get_file_handler_class_THEN_hdf4_handler_returned(self):
        filename = 'hdf_file_test_name.hdf'
        handler = self.handler_factory.get_handler_class(filename)
        assert handler.__name__ == "HDF4"

    def test_GIVEN_cloudsat_filename_WHEN_get_file_handler_class_THEN_cloudsat_handler_returned(self):
        # Matches r'.*_CS_.*GRANULE.*\.hdf'
        filename = 'CLOUDSAT_CS_TEST_DATA_FILENAME_GRANULE.2014.hdf'
        handler = self.handler_factory.get_handler_class(filename)
        assert handler.__name__ == "CloudSat"
