""" Unit testing for CWFIS grass curing data processing """

import asyncio
import os
from contextlib import asynccontextmanager
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import numpy as np
import pytest
from pytest_mock import MockerFixture
from wps_shared.geospatial.geospatial import WGS84

from app.jobs import grass_curing
from app.jobs.grass_curing import (
    CWFIS_BASE_URL,
    GRASS_CURING_FILE_NAME_3978,
    GRASS_CURING_FILE_NAME_4326,
    GrassCuringFileNotFoundException,
    GrassCuringJob,
)


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
    return mock_ds


def test_grass_curing_job_fail(mocker: MockerFixture, monkeypatch):
    """
    Test that when the bot fails, a message is sent to rocket-chat, and our exit code is 1.
    """

    async def mock__run_grass_curing(self):
        raise OSError("Error")

    monkeypatch.setattr(GrassCuringJob, '_run_grass_curing', mock__run_grass_curing)
    rocket_chat_spy = mocker.spy(grass_curing, 'send_rocketchat_notification')

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
    rocket_chat_spy = mocker.spy(grass_curing, "send_rocketchat_notification")

    with pytest.raises(SystemExit) as excinfo:
        grass_curing.main()

    assert excinfo.value.code == os.EX_OK
    assert rocket_chat_spy.call_count == 0


def test_yield_value_for_stations_returns_correct_pixel_values():
    """Test that station coordinates are mapped to the correct raster pixel values."""
    # 3x3 grid, origin (-130, 60), 1-degree pixels north-up.
    # forward: x = col - 130, y = -row + 60
    # inverse: col = lon + 130, row = 60 - lat
    data = np.array(
        [
            [10, 20, 30],
            [40, 50, 60],
            [70, 80, 90],
        ]
    )
    geo_transform = (-130.0, 1.0, 0.0, 60.0, 0.0, -1.0)
    mock_ds = _make_mock_data_source(data, geo_transform)

    stations = [
        SimpleNamespace(code=1, long=-130.0, lat=60.0),  # col=0, row=0 → 10
        SimpleNamespace(code=2, long=-129.0, lat=59.0),  # col=1, row=1 → 50
        SimpleNamespace(code=3, long=-128.0, lat=58.0),  # col=2, row=2 → 90
    ]

    results = list(GrassCuringJob()._yield_value_for_stations(mock_ds, stations))

    assert results == [(1, 10), (2, 50), (3, 90)]


def test_yield_value_for_stations_floors_fractional_pixel_coordinates():
    """Test that sub-pixel coordinates are floored to the containing pixel."""
    data = np.array(
        [
            [10, 20],
            [30, 40],
        ]
    )
    geo_transform = (-130.0, 1.0, 0.0, 60.0, 0.0, -1.0)
    mock_ds = _make_mock_data_source(data, geo_transform)

    # col = floor(-129.9 + 130) = floor(0.1) = 0, row = floor(60 - 59.9) = floor(0.1) = 0
    stations = [SimpleNamespace(code=1, long=-129.9, lat=59.9)]

    results = list(GrassCuringJob()._yield_value_for_stations(mock_ds, stations))

    assert results == [(1, 10)]


def test_reproject_to_epsg_4326_calls_gdal_with_correct_paths(mocker: MockerFixture):
    """Test that _reproject_to_epsg_4326 opens the 3978 source and warps to a 4326 destination."""
    mock_ds = MagicMock()
    mock_gdal_open = mocker.patch("app.jobs.grass_curing.gdal.Open", return_value=mock_ds)
    mock_gdal_warp = mocker.patch("app.jobs.grass_curing.gdal.Warp")

    GrassCuringJob()._reproject_to_epsg_4326("/tmp")

    mock_gdal_open.assert_called_once_with(
        f"/tmp/{GRASS_CURING_FILE_NAME_3978}", grass_curing.gdal.GA_ReadOnly
    )
    mock_gdal_warp.assert_called_once_with(
        f"/tmp/{GRASS_CURING_FILE_NAME_4326}", mock_ds, dstSRS=WGS84
    )


def test_process_grass_curing_saves_value_per_station(mocker: MockerFixture, monkeypatch):
    """Test that _process_grass_curing saves one record per station returned by the API."""

    async def mock_get_raster(self, path):
        pass

    def mock_reproject(self, path):
        pass

    monkeypatch.setattr(GrassCuringJob, "_get_grass_curing_raster", mock_get_raster)
    monkeypatch.setattr(GrassCuringJob, "_reproject_to_epsg_4326", mock_reproject)

    stations = [
        SimpleNamespace(code=1, long=-130.0, lat=60.0, name="Station A"),
        SimpleNamespace(code=2, long=-129.0, lat=59.0, name="Station B"),
    ]

    mock_wfwx_api = MagicMock()
    mock_wfwx_api.get_station_data = AsyncMock(return_value=stations)
    mocker.patch("app.jobs.grass_curing.WfwxApi", return_value=mock_wfwx_api)

    data = np.array([[10, 20], [30, 40]])
    mock_raster = _make_mock_data_source(data, (-130.0, 1.0, 0.0, 60.0, 0.0, -1.0))
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
