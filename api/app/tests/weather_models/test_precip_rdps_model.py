import os
import numpy as np
import pytest
from pytest_mock import MockerFixture
from datetime import datetime, timezone
from unittest.mock import patch
from app.tests.utils.raster_reader import read_raster_array

from app.weather_models.precip_rdps_model import (
    TemporalPrecip,
    compute_and_store_precip_rasters,
    compute_precip_difference,
    get_raster_keys_to_diff,
    generate_24_hour_accumulating_precip_raster,
)
from wps_shared.sfms.rdps_filename_marshaller import model_run_for_hour

geotransform = (-4556441.403315245, 10000.0, 0.0, 920682.1411659503, 0.0, -10000.0)
projection = 'PROJCS["unnamed",GEOGCS["Coordinate System imported from GRIB file",DATUM["unnamed",SPHEROID["Sphere",6371229,0]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]]],PROJECTION["Polar_Stereographic"],PARAMETER["latitude_of_origin",60],PARAMETER["central_meridian",249],PARAMETER["false_easting",0],PARAMETER["false_northing",0],UNIT["Metre",1],AXIS["Easting",SOUTH],AXIS["Northing",SOUTH]]'


def test_difference_identity():
    """
    Verify difference of accumulated precip is zero when diffing the same raster
    """
    parent_dir = os.path.dirname(__file__)
    precip_raster = read_raster_array(os.path.join(parent_dir, "CMC_reg_APCP_SFC_0_ps10km_2024061218_P001.grib2"))
    later_precip = TemporalPrecip(datetime.fromisoformat("2024-06-10T18:42:49"), precip_raster)
    earlier_precip = TemporalPrecip(datetime.fromisoformat("2024-06-09T18:42:49"), precip_raster)

    res = compute_precip_difference(later_precip, earlier_precip)
    assert np.allclose(res, np.zeros(precip_raster.shape))


def test_negative_precip_diff_raises_value_error():
    """
    Verify ValueError raised if raster subtraction contains a negative value.
    """
    later_precip = TemporalPrecip(datetime.fromisoformat("2024-06-10T18:42:49"), np.zeros(1))
    earlier_precip = TemporalPrecip(datetime.fromisoformat("2024-06-09T18:42:49"), np.ones(1))
    with pytest.raises(ValueError):
        compute_precip_difference(later_precip, earlier_precip)


def test_trivial_negative_precip_diff_returns_zero():
    """
    Verify that a negative precip dif between -0.01 and 0 returns 0.
    """
    early_array = np.empty(1)
    early_array[0] = 0.005
    later_precip = TemporalPrecip(datetime.fromisoformat("2024-06-10T18:42:49"), np.zeros(1))
    earlier_precip = TemporalPrecip(datetime.fromisoformat("2024-06-09T18:42:49"), early_array)
    result = compute_precip_difference(later_precip, earlier_precip)
    assert result[0] == 0


@pytest.mark.parametrize(
    "later_datetime,earlier_datetime",
    [
        (datetime.fromisoformat("2024-06-10T18:42:49"), datetime.fromisoformat("2024-06-10T18:42:49")),  # same datetime
        (datetime.fromisoformat("2024-06-09T18:42:49"), datetime.fromisoformat("2024-06-10T18:42:49")),  # later earlier than earlier
    ],
)
def test_temporal_assertion_failures(later_datetime, earlier_datetime):
    """
    Verify ValueError raised for wrong datetime arguments
    """
    parent_dir = os.path.dirname(__file__)
    precip_raster = read_raster_array(os.path.join(parent_dir, "CMC_reg_APCP_SFC_0_ps10km_2024061218_P001.grib2"))
    later_precip = TemporalPrecip(later_datetime, precip_raster)
    earlier_precip = TemporalPrecip(earlier_datetime, precip_raster)

    with pytest.raises(ValueError) as excinfo:
        compute_precip_difference(later_precip, earlier_precip)

    assert excinfo.value.args[0] == "Later precip value must be after earlier precip value"


@pytest.mark.anyio
async def test_generate_24_hour_accumulating_precip_raster_ok(mocker: MockerFixture):
    """
    Verify that the appropriate rasters are diffed correctly for non model hour.
    """
    mocker.patch("app.weather_models.precip_rdps_model.read_into_memory", side_effect=[(np.array([1, 1]), geotransform, projection), (np.array([1, 1]), geotransform, projection)])
    (res, _, _) = await generate_24_hour_accumulating_precip_raster(datetime(2024, 1, 1, 1, tzinfo=timezone.utc))
    assert np.allclose(res, np.array([0, 0]))


@pytest.mark.anyio
async def test_generate_24_hour_accumulating_precip_raster_model_hour_ok(mocker: MockerFixture):
    """
    Verify that the appropriate rasters are diffed correctly on a model hour -- just returns todays data.
    """
    mocker.patch("app.weather_models.precip_rdps_model.read_into_memory", side_effect=[(np.array([1, 1]), geotransform, projection), (np.array([1, 1]), geotransform, projection)])
    (res, _, _) = await generate_24_hour_accumulating_precip_raster(datetime(2024, 1, 1, 0, tzinfo=timezone.utc))
    assert np.allclose(res, np.array([1, 1]))


@pytest.mark.parametrize(
    "current_time,today_raster,yesterday_raster",
    [
        (datetime(2024, 1, 1, 0, tzinfo=timezone.utc), (None, None, None), (np.array([1, 1]), geotransform, projection)),  # no today raster data
        (datetime(2024, 1, 1, 0, tzinfo=timezone.utc), (None, None, None), (None, None, None)),  # no raster data
    ],
)
@pytest.mark.anyio
async def test_generate_24_hour_accumulating_precip_raster_no_today_raster(current_time: datetime, today_raster: np.ndarray, yesterday_raster: np.ndarray, mocker: MockerFixture):
    """
    Verify that the appropriate rasters are diffed correctly.
    """
    mocker.patch("app.weather_models.precip_rdps_model.read_into_memory", side_effect=[today_raster, yesterday_raster])
    (day_data, day_geotransform, day_projection) = await generate_24_hour_accumulating_precip_raster(current_time)
    assert day_data is None
    assert day_geotransform is None
    assert day_projection is None


@pytest.mark.parametrize(
    "hour,expected_model_run",
    [
        (1, 0),  # before noon is 00:00 model run
        (0, 0),
        (13, 12),  # after noon is 12:00 model run
        (12, 12),
    ],
)
def test_model_run_for_hour_ok(hour: int, expected_model_run: int):
    assert model_run_for_hour(hour) == expected_model_run


@pytest.mark.parametrize(
    "timestamp,expected_yesterday_key,expected_today_key",
    [
        # 0 model run, 0:00 UTC hour, grab data from stored RDPS model raster
        (
            datetime(2024, 1, 1, 0, tzinfo=timezone.utc),
            None,
            "weather_models/rdps/2023-12-31/00/precip/CMC_reg_APCP_SFC_0_ps10km_2023123100_P024.grib2",
        ),
        # 12 model run, 12:00 UTC hour grab data from stored RDPS model raster
        (
            datetime(2024, 1, 1, 12, tzinfo=timezone.utc),
            None,
            "weather_models/rdps/2023-12-31/12/precip/CMC_reg_APCP_SFC_0_ps10km_2023123112_P024.grib2",
        ),
        # 0 model run, hour 1:00 UTC, grab data from stored RDPS model raster
        (
            datetime(2024, 1, 1, 1, tzinfo=timezone.utc),
            "weather_models/rdps/2023-12-31/00/precip/CMC_reg_APCP_SFC_0_ps10km_2023123100_P001.grib2",
            "weather_models/rdps/2023-12-31/00/precip/CMC_reg_APCP_SFC_0_ps10km_2023123100_P025.grib2",
        ),
        # 0 model run, hour 2:00 UTC, grab data from stored RDPS model raster
        (
            datetime(2024, 1, 1, 2, tzinfo=timezone.utc),
            "weather_models/rdps/2023-12-31/00/precip/CMC_reg_APCP_SFC_0_ps10km_2023123100_P002.grib2",
            "weather_models/rdps/2023-12-31/00/precip/CMC_reg_APCP_SFC_0_ps10km_2023123100_P026.grib2",
        ),
        # 12 model run, 13:00 UTC hour, grab data from stored RDPS model raster
        (
            datetime(2024, 1, 1, 13, tzinfo=timezone.utc),
            "weather_models/rdps/2023-12-31/12/precip/CMC_reg_APCP_SFC_0_ps10km_2023123112_P001.grib2",
            "weather_models/rdps/2023-12-31/12/precip/CMC_reg_APCP_SFC_0_ps10km_2023123112_P025.grib2",
        ),
        # Test prediction into the future from today. Today = 2024-01-01 01:00 UTC, predict for 2024-01-02 2:00 UTC
        (
            datetime(2024, 1, 2, 2, tzinfo=timezone.utc),
            "weather_models/rdps/2024-01-01/00/precip/CMC_reg_APCP_SFC_0_ps10km_2024010100_P002.grib2",
            "weather_models/rdps/2024-01-01/00/precip/CMC_reg_APCP_SFC_0_ps10km_2024010100_P026.grib2",
        ),
    ],
)
def test_get_raster_keys_to_diff(timestamp: datetime, expected_yesterday_key, expected_today_key):
    """
    Verify that the appropriate rasters are diffed correctly.
    """
    (yesterday_key, today_key) = get_raster_keys_to_diff(timestamp)
    assert yesterday_key == expected_yesterday_key
    assert today_key == expected_today_key


async def return_none_tuple(timestamp: datetime):
    return (None, None, None)


@patch("app.weather_models.precip_rdps_model.generate_24_hour_accumulating_precip_raster", return_none_tuple)
@pytest.mark.anyio
async def test_compute_and_store_precip_rasters_no_today_data_does_not_throw():
    timestamp = datetime.fromisoformat("2024-06-10T18:42:49+00:00")
    await compute_and_store_precip_rasters(timestamp)
