import os
from datetime import datetime

import pytest
from pytest_mock import MockerFixture

import wps_jobs.fuel_raster
from wps_jobs.fuel_raster import start_job
from wps_shared.db.models import FuelTypeRaster
from wps_shared.sfms.raster_addresser import RasterKeyAddresser

START_TIMESTAMP = datetime(2024, 1, 1)
CREATE_TIMESTAMP = datetime(2024, 4, 15, 12, 0)


# --- Mocked S3Client with async methods ---
class MockS3Client:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        pass

    # Mocked async methods for S3Client
    async def copy_object(self, src, dst):
        assert src == "unprocessed-key"  # Test we call it with the correct key
        assert dst == "fuel-key-v3"  # Test the new key is generated correctly

    async def get_content_hash(self, _):
        return "abc123"

    async def get_fuel_raster(self, key, hash_):
        return b"raster-bytes"  # Fake raster content for testing


# WPSDataset.from_bytes context manager
class MockRaster:
    def as_gdal_ds(self):
        class GDAL:
            RasterXSize = 100
            RasterYSize = 200

        return GDAL()


class MockRasterContext:
    def __enter__(self):
        return MockRaster()

    def __exit__(self, *a):
        pass


class MockDB:
    def __init__(self):
        self.added = {}

    class MockDBSession:
        def __init__(self, outer):
            self.outer = outer

        def add(self, obj):
            self.outer.added["raster"] = obj

    class MockDBScope:
        def __init__(self, outer):
            self.outer = outer

        async def __aenter__(self):
            return MockDB.MockDBSession(self.outer)

        async def __aexit__(self, *a):
            pass


def setup_mocks(monkeypatch):
    def mock_get_unprocessed_key(_):
        return "unprocessed-key"

    def mock_get_fuel_key(_, version):
        return f"fuel-key-v{version}"

    async def mock_process_fuel_type_raster(_, __, ___):
        return (START_TIMESTAMP.year, 3, 100, 200, "fuel-key-v3", "abc123", CREATE_TIMESTAMP)

    monkeypatch.setattr(
        "wps_jobs.fuel_raster.process_fuel_type_raster", mock_process_fuel_type_raster
    )

    raster_addresser = RasterKeyAddresser()
    monkeypatch.setattr(
        raster_addresser, "get_unprocessed_fuel_raster_key", mock_get_unprocessed_key
    )
    monkeypatch.setattr(raster_addresser, "get_fuel_raster_key", mock_get_fuel_key)

    monkeypatch.setattr("wps_shared.fuel_raster.S3Client", lambda: MockS3Client())

    async def mock_find_latest_version(_, __, ___, ____):
        return 2

    monkeypatch.setattr("wps_shared.fuel_raster.find_latest_version", mock_find_latest_version)

    monkeypatch.setattr(
        "wps_shared.fuel_raster.WPSDataset.from_bytes", lambda res: MockRasterContext()
    )

    mock_db = MockDB()
    monkeypatch.setattr(
        "wps_jobs.fuel_raster.get_async_write_session_scope", lambda: mock_db.MockDBScope(mock_db)
    )

    # UTC now
    monkeypatch.setattr("wps_shared.fuel_raster.get_utc_now", lambda: CREATE_TIMESTAMP)
    return raster_addresser, mock_db


@pytest.mark.anyio
async def test_start_job_success(monkeypatch):
    raster_addresser, mock_db = setup_mocks(monkeypatch)

    await start_job(
        raster_addresser=raster_addresser,
        start_datetime=datetime(2024, 1, 1),
        unprocessed_object_name="fuel.tif",
    )

    raster = mock_db.added["raster"]
    assert isinstance(raster, FuelTypeRaster)
    assert raster.xsize == 100
    assert raster.ysize == 200
    assert raster.content_hash == "abc123"
    assert raster.object_store_path == "fuel-key-v3"


@pytest.mark.anyio
async def test_start_job_failure(monkeypatch):
    raster_addresser, mock_db = setup_mocks(monkeypatch)

    async def mock_process_fuel_type_raster_value_error(_, __, ___):
        raise ValueError("error")

    monkeypatch.setattr(
        "wps_jobs.fuel_raster.process_fuel_type_raster", mock_process_fuel_type_raster_value_error
    )

    with pytest.raises(ValueError):
        await start_job(
            raster_addresser=raster_addresser,
            start_datetime=datetime(2024, 1, 1),
            unprocessed_object_name="fuel.tif",
        )


def test_main_fail(mocker: MockerFixture, monkeypatch):
    async def mock_start_job(_, __, ___, ____):
        raise Exception()

    rocket_chat_spy = mocker.spy(wps_jobs.fuel_raster, "send_rocketchat_notification")
    monkeypatch.setattr(wps_jobs.fuel_raster, "start_job", mock_start_job)

    with pytest.raises(SystemExit) as excinfo:
        wps_jobs.fuel_raster.main()

    # Assert that we exited with an error code.
    assert excinfo.value.code == os.EX_SOFTWARE
    # Assert that rocket chat was called.
    assert rocket_chat_spy.call_count == 1


def test_main_success(mocker: MockerFixture, monkeypatch):
    async def mock_start_job(_, __, ___):
        pass

    rocket_chat_spy = mocker.spy(wps_jobs.fuel_raster, "send_rocketchat_notification")
    monkeypatch.setattr(wps_jobs.fuel_raster, "start_job", mock_start_job)

    with pytest.raises(SystemExit) as excinfo:
        wps_jobs.fuel_raster.main()

    # Assert that we exited with an error code.
    assert excinfo.value.code == os.EX_OK

    # Assert that rocket chat was called.
    assert rocket_chat_spy.call_count == 0
