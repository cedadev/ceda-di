"""
Module that contains information about the test data
"""

from datetime import datetime
from cis.test.integration_test_data import TestFileTestData

import os

# A dictionary of test file tuples indexed by characteristic name
ceda_di_test_files = {}


def make_pathname(filename):
    return os.path.join(os.path.dirname(__file__), filename)

ceda_di_test_files["cloudsat_PRECIP_2007"] = TestFileTestData(
    master_filename=make_pathname('2007189224156_06358_CS_2C-PRECIP-COLUMN_GRANULE_P_R04_E02.hdf'),
    file_format="HDF4/CloudSat",
    product_name="CloudSat",
    start_datetime=datetime(2007, 7, 8, 22, 42, 2),
    end_datetime=datetime(2007, 7, 9, 0, 20, 55),
    lat_min=-81.851,
    lat_max=81.851,
    lon_min=-179.992,
    lon_max=179.992,
    valid_vars_count=34,
    all_variable_names=None,
    data_variable_name='DEM_elevation',
    data_variable_standard_name='DEM_elevation',
    data_variable_properties={
        "long_name": "Digital Elevation Map",
        "standard_name": "DEM_elevation",
        "shape": [37082],
        "factor": 1.0,
        "units": 'meters',
        "calendar": '',
        "missing_value": 9999,
        "history": '',
        "range": [-9999, 8850],
        "offset": 0.0})
