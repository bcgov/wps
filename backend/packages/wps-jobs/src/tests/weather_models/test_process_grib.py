import math
import os
from datetime import datetime
from unittest.mock import MagicMock

import pytest
from aiohttp import ClientSession
from osgeo import gdal
from pyproj import CRS
from weather_model_jobs.utils import process_grib
from wps_shared.geospatial.geospatial import NAD83_CRS
from wps_shared.tests.common import default_mock_client_get
from wps_shared.weather_models import ModelEnum


def test_convert_mps_to_kph():
    metres_per_second_speed = 1
    kilometres_per_hour_speed = process_grib.convert_mps_to_kph(metres_per_second_speed)
    assert math.isclose(
        kilometres_per_hour_speed, 3.6, abs_tol=0.1
    )  # 1m/s * 3600 sec/hour / 1000m/km


def test_convert_mps_to_kph_zero_wind_speed():
    metres_per_second_speed = 0
    kilometres_per_hour_speed = process_grib.convert_mps_to_kph(metres_per_second_speed)
    assert kilometres_per_hour_speed == 0


@pytest.mark.parametrize(
    "variable_name,expected",
    [
        ("AirTemp_AGL-2m", "tmp_tgl_2"),
        ("RelativeHumidity_AGL-2m", "rh_tgl_2"),
        ("Precip-Accum_Sfc", "apcp_sfc_0"),
        ("WindSpeed_AGL-10m", "wind_tgl_10"),
        ("WindDir_AGL-10m", "wdir_tgl_10"),
        ("TMP_TGL_2", "tmp_tgl_2"),
    ],
)
def test_get_variable_name_maps_gdps_filename_variables(variable_name, expected):
    grib_info = process_grib.ModelRunInfo(
        model_enum=ModelEnum.GDPS,
        variable_name=variable_name,
    )
    processor = process_grib.GribFileProcessor.__new__(process_grib.GribFileProcessor)

    assert processor.get_variable_name(grib_info) == expected


def test_read_single_raster_value(monkeypatch: pytest.MonkeyPatch):
    """
    Verified with gdallocationinfo 20260602T00Z_MSC_GDPS_AirTemp_AGL-2m_LatLon0.15_PT000H.grib2 -wgs84 -120.4816667 50.6733333
    """
    monkeypatch.setattr(ClientSession, "get", default_mock_client_get)
    filename = os.path.join(
        os.path.dirname(__file__), "20260602T00Z_MSC_GDPS_AirTemp_AGL-2m_LatLon0.15_PT000H.grib2"
    )
    dataset = gdal.Open(filename, gdal.GA_ReadOnly)

    # Ensure that grib file uses EPSG:4269 (NAD83) coordinate system
    # (this step is included because HRDPS grib files are in another coordinate system)
    wkt = dataset.GetProjection()
    crs = CRS.from_string(wkt)
    raster_to_geo_transformer = process_grib.get_transformer(crs, NAD83_CRS)
    geo_to_raster_transformer = process_grib.get_transformer(NAD83_CRS, crs)
    padf_transform = process_grib.get_dataset_transform(filename)

    processor = process_grib.GribFileProcessor(
        padf_transform, raster_to_geo_transformer, geo_to_raster_transformer
    )

    raster_band = dataset.GetRasterBand(1)
    station, value = next(processor.yield_value_for_stations(raster_band))

    assert station.code == 995
    assert math.isclose(value, 21.893, abs_tol=0.001)

    del dataset


def _make_mock_session_with_no_existing_prediction():
    session = MagicMock()
    session.query.return_value.filter.return_value.filter.return_value.filter.return_value.first.return_value = None
    return session


def test_store_prediction_value_expunges_new_prediction_after_commit():
    """A new prediction is committed and then expunged from the session, so the session's
    identity map doesn't accumulate one entry per station per grib file for the life of the
    run."""
    processor = process_grib.GribFileProcessor.__new__(process_grib.GribFileProcessor)
    session = _make_mock_session_with_no_existing_prediction()
    prediction_model_run = MagicMock()
    prediction_model_run.id = 42
    grib_info = process_grib.ModelRunInfo(
        model_enum=ModelEnum.GDPS,
        variable_name="AirTemp_AGL-2m",
        prediction_timestamp=datetime(2026, 6, 2, 0, 0, 0),
    )

    processor.store_prediction_value(995, 21.9, prediction_model_run, grib_info, session)

    session.commit.assert_called_once()
    session.expunge.assert_called_once()
    (expunged_prediction,) = session.expunge.call_args[0]
    added_prediction = session.add.call_args[0][0]
    assert expunged_prediction is added_prediction
    assert math.isclose(expunged_prediction.tmp_tgl_2, 21.9, abs_tol=0.001)

    # commit must happen before expunge, otherwise the row would be dropped before it's saved.
    call_names = [call[0] for call in session.mock_calls]
    assert call_names.index("commit") < call_names.index("expunge")


def test_store_prediction_value_expunges_existing_prediction_after_commit():
    """Same as above, but for the update-an-existing-row path."""
    processor = process_grib.GribFileProcessor.__new__(process_grib.GribFileProcessor)
    existing_prediction = MagicMock()
    session = MagicMock()
    session.query.return_value.filter.return_value.filter.return_value.filter.return_value.first.return_value = existing_prediction
    prediction_model_run = MagicMock()
    prediction_model_run.id = 42
    grib_info = process_grib.ModelRunInfo(
        model_enum=ModelEnum.GDPS,
        variable_name="AirTemp_AGL-2m",
        prediction_timestamp=datetime(2026, 6, 2, 0, 0, 0),
    )

    processor.store_prediction_value(995, 21.9, prediction_model_run, grib_info, session)

    session.commit.assert_called_once()
    session.expunge.assert_called_once_with(existing_prediction)
