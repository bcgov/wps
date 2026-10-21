from datetime import datetime, timezone

import pytest

from wps_shared.sfms.raster_addresser import BaseRasterAddresser, S3Key

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


def test_get_fire_zone_units_path(addresser: BaseRasterAddresser):
    result = addresser.get_fire_zone_units_path()
    assert result == f"{addresser.s3_prefix}/zone-units/fire_zone_units.tif"


def test_gdal_path(addresser: BaseRasterAddresser):
    key = S3Key("sfms/static/fuel/2026/fbp2026_v1.tif")
    result = addresser.gdal_path(key)
    assert result == f"{addresser.s3_prefix}/{key}"


def test_s3_key_strips_the_gdal_prefix(addresser: BaseRasterAddresser):
    assert addresser.s3_key(f"{addresser.s3_prefix}/sfms/static/bc_mask.tif") == (
        "sfms/static/bc_mask.tif"
    )


def test_s3_key_passes_plain_keys_through(addresser: BaseRasterAddresser):
    assert addresser.s3_key("sfms/static/bc_mask.tif") == "sfms/static/bc_mask.tif"


def test_s3_key_reverses_gdal_path(addresser: BaseRasterAddresser):
    key = S3Key("sfms_ng/actual/2024/10/10/ffmc_20241010.tif")
    assert addresser.s3_key(addresser.gdal_path(key)) == key


def test_gdal_prefix_keys_prefixes_each_key_in_order(addresser: BaseRasterAddresser):
    assert addresser.gdal_prefix_keys(S3Key("a.tif"), S3Key("b/c.tif")) == (
        f"{addresser.s3_prefix}/a.tif",
        f"{addresser.s3_prefix}/b/c.tif",
    )


def test_gdal_prefix_keys_with_no_keys_is_empty(addresser: BaseRasterAddresser):
    assert addresser.gdal_prefix_keys() == ()


def test_get_fuel_raster_key(addresser: BaseRasterAddresser):
    result = addresser.get_fuel_raster_key(TEST_DATETIME, 1)
    assert result == f"sfms/static/fuel/{TEST_DATETIME.year}/fbp{TEST_DATETIME.year}_v1.tif"


def test_get_unprocessed_raster_key(addresser: BaseRasterAddresser):
    result = addresser.get_unprocessed_fuel_raster_key("test.tif")
    assert result == "sfms/static/test.tif"


def test_get_percent_conifer_key(addresser: BaseRasterAddresser):
    result = addresser.get_percent_conifer_key(2024)
    assert result == "sfms/static/m12_2024.tif"


def test_get_percent_dead_conifer_key(addresser: BaseRasterAddresser):
    result = addresser.get_percent_dead_conifer_key(2024)
    assert result == "sfms/static/m34_2024.tif"
