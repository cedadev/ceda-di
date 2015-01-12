from unittest import TestCase
from ceda_di.extract import HandlerFactory
from hamcrest import *
from ceda_di.metadata.product import FileFormatError


class TestHandlerFactory(TestCase):
    """
    Tests that the HandlerFactory can correctly identify the handler
    to instantiate given a filename.
    """

    def setUp(self):
        handler_map = {
            "_nav_post_processed.bil.hdr$": {
                "class": "ceda_di.providers.arsf.envi.BIL",
                "priority": 10
            },
            ".hdf$": {
                "class": "ceda_di.providers.arsf.hdf4.HDF4",
                "priority": 10
            },
            ".tif$": {
                "class": "ceda_di.providers.arsf.exif.EXIF",
                "priority": 10
            },
            ".nc$": {
                "class": "ceda_di.jascis.JasCisDataProduct",
                "priority": 1
            },
            ".*_CS_.*GRANULE.*\\.hdf$": {
                "class": "ceda_di.jascis.JasCisDataProduct",
                "priority": 1
            },
            ".*\.never$": {
                "class": "test.test_handler_factory.Never",
                "priority": 1
            },
            ".*\.always$": {
                "class": "test.test_handler_factory.Always",
                "priority": 1
            }
        }
        self.handler_factory = HandlerFactory(handler_map)

    def test_GIVEN_bil_filename_WHEN_get_file_handler_class_THEN_bil_handler_returned(self):
        filename = 'test_nav_post_processed.bil.hdr'
        handler = self.handler_factory.get_handler_class(filename)
        assert_that(handler.__name__, is_("BIL"))

    def test_GIVEN_exif_filename_WHEN_get_file_handler_class_THEN_exif_handler_returned(self):
        filename = 'exif_file_test_name.tif'
        handler = self.handler_factory.get_handler_class(filename)
        assert_that(handler.__name__, is_("EXIF"))

    def test_GIVEN_hdf_filename_WHEN_get_file_handler_class_THEN_hdf4_handler_returned(self):
        filename = 'hdf_file_test_name.hdf'
        handler = self.handler_factory.get_handler_class(filename)
        assert_that(handler.__name__, is_("HDF4"))

    def test_GIVEN_cloudsat_filename_WHEN_get_file_handler_class_THEN_cloudsat_handler_returned(self):
        # Matches r'.*_CS_.*GRANULE.*\.hdf'
        filename = 'CLOUDSAT_CS_TEST_DATA_FILENAME_GRANULE.2014.hdf'
        handler = self.handler_factory.get_handler_class(filename)
        assert_that(handler.__name__, is_("JasCisDataProduct"))

    def test_GIVEN_never_WHEN_get_file_handler_class_THEN_unknown_class_returned(self):

        filename = 'blah.never'
        handler = self.handler_factory.get_handler_class(filename)
        assert_that(handler, is_(None), "No product should be returned")

    def test_GIVEN_always_WHEN_get_file_handler_class_THEN_always_returned(self):

        filename = 'blah.always'
        handler = self.handler_factory.get_handler_class(filename)
        assert_that(handler.__name__, is_("Always"))


class Never():
    @staticmethod
    def get_file_format(filename):
        raise FileFormatError(["bad"])


class Always():
    @staticmethod
    def get_file_format(filename):
        return "Always"
