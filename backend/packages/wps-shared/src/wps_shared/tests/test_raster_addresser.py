from datetime import datetime, timezone

import pytest

from wps_shared.sfms.raster_addresser import BaseRasterAddresser

TEST_DATETIME = datetime(2024, 10, 10, 6, tzinfo=timezone.utc)


@pytest.fixture
def addresser():
    return BaseRasterAddresser()


def test_get_cog_key_success(addresser: BaseRasterAddresser):
    result = addresser.get_cog_key("test.tif")
    assert result == "/vsis3/some bucket/test_cog.tif"


def test_get_cog_key_failed(addresser: BaseRasterAddresser):
    with pytest.raises(Exception):
        addresser.get_cog_key("test.gif")


def test_get_dem_key(addresser: BaseRasterAddresser):
    result = addresser.get_dem_key()
    assert result == f"{addresser.s3_prefix}/sfms/static/bc_elevation.tif"


def test_get_mask_key(addresser: BaseRasterAddresser):
    result = addresser.get_mask_key()
    assert result == f"{addresser.s3_prefix}/sfms/static/bc_mask.tif"


def test_get_fuel_raster_key(addresser: BaseRasterAddresser):
    result = addresser.get_fuel_raster_key(TEST_DATETIME, 1)
    assert result == f"sfms/static/fuel/{TEST_DATETIME.year}/fbp{TEST_DATETIME.year}_v1.tif"


def test_get_unprocessed_raster_key(addresser: BaseRasterAddresser):
    result = addresser.get_unprocessed_fuel_raster_key("test.tif")
    assert result == "sfms/static/test.tif"
