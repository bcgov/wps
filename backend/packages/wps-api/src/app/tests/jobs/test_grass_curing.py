""" Unit testing for CWFIS grass curing data processing """

import asyncio
import math
import os
from contextlib import asynccontextmanager
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import numpy as np
import pytest
from osgeo import osr
from pytest_mock import MockerFixture
from wps_shared.geospatial.geospatial import SpatialReferenceSystem

from app.jobs import grass_curing
from app.jobs.grass_curing import (
    CWFIS_BASE_URL,
    GRASS_CURING_FILE_NAME_3978,
    GrassCuringFileNotFoundException,
    GrassCuringJob,
)

_bc_albers_srs = osr.SpatialReference()
_bc_albers_srs.ImportFromEPSG(SpatialReferenceSystem.NAD83_BC_ALBERS.code)
_bc_albers_srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
BC_ALBERS_WKT = _bc_albers_srs.ExportToWkt()

_wgs84_srs = osr.SpatialReference()
_wgs84_srs.ImportFromEPSG(SpatialReferenceSystem.WGS84.code)
_wgs84_srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)

_wgs84_to_bc_albers = osr.CoordinateTransformation(_wgs84_srs, _bc_albers_srs)


def _make_mock_client_session(mocker: MockerFixture, content: bytes = b"fake tiff bytes"):
    mock_response = AsyncMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.read = AsyncMock(return_value=content)
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)

    mock_session = MagicMock()
    mock_session.get = MagicMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    mocker.patch("app.jobs.grass_curing.ClientSession", return_value=mock_session)
    return mock_session, mock_response


def _make_mock_data_source(data: np.ndarray, geo_transform: tuple):
    """Build a mock gdal data source from a numpy array and a GDAL geotransform tuple."""
    mock_band = MagicMock()
    mock_band.ReadAsArray.return_value = data
    mock_ds = MagicMock()
    mock_ds.GetRasterBand.return_value = mock_band
    mock_ds.GetGeoTransform.return_value = geo_transform
    mock_ds.GetProjection.return_value = BC_ALBERS_WKT
    return mock_ds


def test_grass_curing_job_fail(mocker: MockerFixture, monkeypatch):
    """
    Test that when the job fails, a message is sent to rocket-chat, and our exit code is 1.
    """

    async def mock__run_grass_curing(self):
        raise OSError("Error")

    monkeypatch.setattr(GrassCuringJob, '_run_grass_curing', mock__run_grass_curing)
    rocket_chat_spy = mocker.spy(grass_curing, 'send_chatops_notification')

    with pytest.raises(SystemExit) as excinfo:
        grass_curing.main()
    assert excinfo.value.code == os.EX_SOFTWARE
    assert rocket_chat_spy.call_count == 1


def test_grass_curing_job_exits_without_error_when_no_work_required(monkeypatch):
    """Test that grass_curing_job exits without error when no data needs to be processed."""
    async def mock__get_last_for_date(self):
        return datetime.now()

    monkeypatch.setattr(GrassCuringJob, "_get_last_for_date", mock__get_last_for_date)

    with pytest.raises(SystemExit) as excinfo:
        grass_curing.main()
    assert excinfo.value.code == os.EX_OK


def test_get_grass_curing_raster_writes_file(mocker: MockerFixture):
    """Test that _get_grass_curing_raster downloads content and writes it to the expected path."""
    fake_content = b"fake tiff bytes"
    mock_session, _ = _make_mock_client_session(mocker, fake_content)

    mock_file = AsyncMock()
    mock_file.__aenter__ = AsyncMock(return_value=mock_file)
    mock_file.__aexit__ = AsyncMock(return_value=None)
    mock_open = mocker.patch("app.jobs.grass_curing.aiofiles.open", return_value=mock_file)

    job = GrassCuringJob()
    loop = asyncio.new_event_loop()
    loop.run_until_complete(job._get_grass_curing_raster("/tmp"))

    expected_url = f"{CWFIS_BASE_URL}/pc{job.grass_cure_datetime.strftime('%Y%m%d')}.tif"
    mock_session.get.assert_called_once_with(expected_url)
    mock_open.assert_called_once_with(os.path.join("/tmp", GRASS_CURING_FILE_NAME_3978), "wb")
    mock_file.write.assert_called_once_with(fake_content)


def test_get_grass_curing_raster_raises_on_http_error(mocker: MockerFixture):
    """Test that _get_grass_curing_raster raises when the server returns an HTTP error."""
    mock_response = AsyncMock()
    mock_response.raise_for_status = MagicMock(side_effect=Exception("500 Server Error"))
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)

    mock_session = MagicMock()
    mock_session.get = MagicMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    mocker.patch("app.jobs.grass_curing.ClientSession", return_value=mock_session)

    loop = asyncio.new_event_loop()
    with pytest.raises(Exception, match="500 Server Error"):
        loop.run_until_complete(GrassCuringJob()._get_grass_curing_raster("/tmp"))


def test_get_grass_curing_raster_raises_file_not_found_on_404(mocker: MockerFixture):
    """Test that _get_grass_curing_raster raises GrassCuringFileNotFoundException on a 404."""
    mock_response = AsyncMock()
    mock_response.status = 404
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)

    mock_session = MagicMock()
    mock_session.get = MagicMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    mocker.patch("app.jobs.grass_curing.ClientSession", return_value=mock_session)

    loop = asyncio.new_event_loop()
    with pytest.raises(GrassCuringFileNotFoundException):
        loop.run_until_complete(GrassCuringJob()._get_grass_curing_raster("/tmp"))


def test_main_exits_cleanly_when_file_not_found(mocker: MockerFixture, monkeypatch):
    """Test that main exits with EX_OK and skips rocket chat when the file is not yet available."""
    async def mock__run_grass_curing(self):
        raise GrassCuringFileNotFoundException("not found")

    monkeypatch.setattr(GrassCuringJob, "_run_grass_curing", mock__run_grass_curing)
    rocket_chat_spy = mocker.spy(grass_curing, "send_chatops_notification")

    with pytest.raises(SystemExit) as excinfo:
        grass_curing.main()

    assert excinfo.value.code == os.EX_OK
    assert rocket_chat_spy.call_count == 0


def test_yield_value_for_stations_returns_correct_pixel_values():
    """Test that WGS84 station coordinates are projected to BC Albers and mapped to correct pixels."""

    # Setup some stations at actual locations in BC. Stations are geographically far apart so no
    # two end up in the same grid cell when making a mock raster.
    stations = [
        SimpleNamespace(code=1, long=-122.7, lat=53.9),  # Prince George area
        SimpleNamespace(code=2, long=-120.3, lat=50.7),  # Kamloops area
        SimpleNamespace(code=3, long=-115.0, lat=49.0),  # Cranbrook area
    ]

    # Using BC Albers as a proxy for the srs of the grass curing tif which is also based on metres.
    bc_albers_coords = [_wgs84_to_bc_albers.TransformPoint(s.long, s.lat)[:2] for s in stations]

    ##################### Start setup a test grid of data
    pixel_size = 100000  # 100 km — stations are well over 100 km apart
    origin_x = min(x for x, _ in bc_albers_coords) - pixel_size
    origin_y = max(y for _, y in bc_albers_coords) + pixel_size
    geo_transform = (origin_x, pixel_size, 0.0, origin_y, 0.0, -pixel_size)

    pixel_indices = [
        (math.floor((x - origin_x) / pixel_size), math.floor((origin_y - y) / pixel_size))
        for x, y in bc_albers_coords
    ]
    assert len(set(pixel_indices)) == len(stations), "test setup error: stations share a pixel"

    n_cols = max(col for col, _ in pixel_indices) + 2
    n_rows = max(row for _, row in pixel_indices) + 2
    data = np.zeros((n_rows, n_cols), dtype=np.int32)
    expected_values = [10, 50, 90]
    for (col, row), val in zip(pixel_indices, expected_values):
        data[row][col] = val

    mock_ds = _make_mock_data_source(data, geo_transform)
    ##################### End setup a test grid of data

    results = list(GrassCuringJob()._yield_value_for_stations(mock_ds, stations))

    assert results == [(1, 10), (2, 50), (3, 90)]


def test_yield_value_for_stations_floors_fractional_pixel_coordinates():
    """Test that sub-pixel BC Albers coordinates are floored to the containing pixel."""
    lon, lat = -120.3, 50.7  # Kamloops area
    x, y, _ = _wgs84_to_bc_albers.TransformPoint(lon, lat)

    # Place origin so the station lands 30% into pixel (col=0, row=0)
    pixel_size = 100_000
    origin_x = x - 0.3 * pixel_size
    origin_y = y + 0.3 * pixel_size
    geo_transform = (origin_x, pixel_size, 0.0, origin_y, 0.0, -pixel_size)

    data = np.array([[42, 99], [77, 33]])
    mock_ds = _make_mock_data_source(data, geo_transform)

    results = list(
        GrassCuringJob()._yield_value_for_stations(
            mock_ds, [SimpleNamespace(code=1, long=lon, lat=lat)]
        )
    )

    assert results == [(1, 42)]  # floored to pixel (col=0, row=0)


def test_yield_value_for_stations_skips_station_west_of_raster():
    """Test that a station west of the raster (px < 0) is skipped rather than wrapping around."""
    lon, lat = -120.3, 50.7  # Kamloops
    x, y, _ = _wgs84_to_bc_albers.TransformPoint(lon, lat)

    pixel_size = 100_000
    # Place origin east of the station so px = floor(-1.0) = -1
    origin_x = x + pixel_size
    origin_y = y + pixel_size
    geo_transform = (origin_x, pixel_size, 0.0, origin_y, 0.0, -pixel_size)

    data = np.array([[42, 99], [77, 33]])
    mock_ds = _make_mock_data_source(data, geo_transform)

    results = list(
        GrassCuringJob()._yield_value_for_stations(
            mock_ds, [SimpleNamespace(code=1, long=lon, lat=lat)]
        )
    )
    assert results == []


def test_yield_value_for_stations_skips_station_north_of_raster():
    """Test that a station north of the raster (py < 0) is skipped rather than wrapping around."""
    lon, lat = -120.3, 50.7  # Kamloops
    x, y, _ = _wgs84_to_bc_albers.TransformPoint(lon, lat)

    pixel_size = 100_000
    # Place origin south of the station so py = floor(-1.0) = -1
    origin_x = x - pixel_size
    origin_y = y - pixel_size
    geo_transform = (origin_x, pixel_size, 0.0, origin_y, 0.0, -pixel_size)

    data = np.array([[42, 99], [77, 33]])
    mock_ds = _make_mock_data_source(data, geo_transform)

    results = list(
        GrassCuringJob()._yield_value_for_stations(
            mock_ds, [SimpleNamespace(code=1, long=lon, lat=lat)]
        )
    )
    assert results == []


def test_yield_value_for_stations_skips_station_east_of_raster():
    """Test that a station east of the raster (px >= cols) is skipped."""
    lon, lat = -120.3, 50.7  # Kamloops
    x, y, _ = _wgs84_to_bc_albers.TransformPoint(lon, lat)

    pixel_size = 100_000
    # origin_x = x - pixel_size puts station at px=1; raster is 1 column wide so px >= cols
    origin_x = x - pixel_size
    origin_y = y + 0.5 * pixel_size  # py=0, inside the single row
    geo_transform = (origin_x, pixel_size, 0.0, origin_y, 0.0, -pixel_size)

    data = np.array([[42]])  # 1 row, 1 col
    mock_ds = _make_mock_data_source(data, geo_transform)

    results = list(
        GrassCuringJob()._yield_value_for_stations(
            mock_ds, [SimpleNamespace(code=1, long=lon, lat=lat)]
        )
    )
    assert results == []


def test_yield_value_for_stations_skips_station_south_of_raster():
    """Test that a station south of the raster (py >= rows) is skipped."""
    lon, lat = -120.3, 50.7  # Kamloops
    x, y, _ = _wgs84_to_bc_albers.TransformPoint(lon, lat)

    pixel_size = 100_000
    # origin_y = y + pixel_size puts station at py=1; raster is 1 row tall so py >= rows
    origin_x = x - 0.5 * pixel_size  # px=0, inside the single column
    origin_y = y + pixel_size
    geo_transform = (origin_x, pixel_size, 0.0, origin_y, 0.0, -pixel_size)

    data = np.array([[42]])  # 1 row, 1 col
    mock_ds = _make_mock_data_source(data, geo_transform)

    results = list(
        GrassCuringJob()._yield_value_for_stations(
            mock_ds, [SimpleNamespace(code=1, long=lon, lat=lat)]
        )
    )
    assert results == []


def test_process_grass_curing_saves_value_per_station(mocker: MockerFixture, monkeypatch):
    """Test that _process_grass_curing saves one record per station returned by the API."""

    async def mock_get_raster(self, path):
        pass

    monkeypatch.setattr(GrassCuringJob, "_get_grass_curing_raster", mock_get_raster)

    stations = [
        SimpleNamespace(code=1, long=-130.0, lat=60.0, name="Station A"),
        SimpleNamespace(code=2, long=-129.0, lat=59.0, name="Station B"),
    ]

    mock_wfwx_api = MagicMock()
    mock_wfwx_api.get_station_data = AsyncMock(return_value=stations)
    mocker.patch("app.jobs.grass_curing.WfwxApi", return_value=mock_wfwx_api)

    bc_albers_coords = [_wgs84_to_bc_albers.TransformPoint(s.long, s.lat)[:2] for s in stations]
    pixel_size = 100_000
    origin_x = min(x for x, _ in bc_albers_coords) - pixel_size
    origin_y = max(y for _, y in bc_albers_coords) + pixel_size
    geo_transform = (origin_x, pixel_size, 0.0, origin_y, 0.0, -pixel_size)
    n_cols = max(math.floor((x - origin_x) / pixel_size) for x, _ in bc_albers_coords) + 2
    n_rows = max(math.floor((origin_y - y) / pixel_size) for _, y in bc_albers_coords) + 2
    data = np.ones((n_rows, n_cols), dtype=np.int32) * 50
    mock_raster = _make_mock_data_source(data, geo_transform)
    mocker.patch("app.jobs.grass_curing.gdal.Open", return_value=mock_raster)

    mock_db_session = MagicMock()

    @asynccontextmanager
    async def mock_write_scope():
        yield mock_db_session

    mocker.patch("app.jobs.grass_curing.get_async_write_session_scope", mock_write_scope)
    mock_save = mocker.patch(
        "app.jobs.grass_curing.save_percent_grass_curing", new_callable=AsyncMock
    )

    _make_mock_client_session(mocker)

    job = GrassCuringJob()
    loop = asyncio.new_event_loop()
    loop.run_until_complete(job._process_grass_curing())

    assert mock_save.call_count == len(stations)
    saved_records = [call.args[1] for call in mock_save.call_args_list]
    assert saved_records[0].station_code == 1
    assert saved_records[1].station_code == 2
    assert all(r.for_date == job.grass_cure_datetime for r in saved_records)


def test_run_grass_curing_triggers_processing_when_no_previous_data(monkeypatch):
    """Test that _run_grass_curing calls _process_grass_curing when last_processed is None."""
    processed = []

    async def mock_get_last_for_date(self):
        return None

    async def mock_process_grass_curing(self):
        processed.append(True)

    monkeypatch.setattr(GrassCuringJob, "_get_last_for_date", mock_get_last_for_date)
    monkeypatch.setattr(GrassCuringJob, "_process_grass_curing", mock_process_grass_curing)

    with pytest.raises(SystemExit) as excinfo:
        grass_curing.main()

    assert excinfo.value.code == os.EX_OK
    assert len(processed) == 1


def test_run_grass_curing_triggers_processing_when_last_processed_before_today(monkeypatch):
    """Test that _run_grass_curing calls _process_grass_curing when last_processed is before today."""
    processed = []

    async def mock_get_last_for_date(self):
        return datetime(2000, 1, 1)

    async def mock_process_grass_curing(self):
        processed.append(True)

    monkeypatch.setattr(GrassCuringJob, "_get_last_for_date", mock_get_last_for_date)
    monkeypatch.setattr(GrassCuringJob, "_process_grass_curing", mock_process_grass_curing)

    with pytest.raises(SystemExit) as excinfo:
        grass_curing.main()

    assert excinfo.value.code == os.EX_OK
    assert len(processed) == 1
