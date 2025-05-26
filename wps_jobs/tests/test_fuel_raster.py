import os
import pytest
from datetime import datetime

from pytest_mock import MockerFixture
import wps_jobs.fuel_raster
from wps_jobs.fuel_raster import find_latest_version, start_job
from wps_shared.sfms.raster_addresser import RasterKeyAddresser
from wps_shared.utils.s3_client import S3Client
from wps_shared.db.models import FuelTypeRaster


@pytest.mark.anyio
@pytest.mark.parametrize(
    "keys",
    [
        # existing versions
        (["raster_v1", "raster_v2", "raster_v3"]),
        # no existing versions
        (["raster_v1"]),
    ],
)
async def test_find_latest_version_non_existing(monkeypatch, keys):
    call_log = []

    # Patch all_objects_exist to simulate
    async def mock_all_objects_exist(key):
        call_log.append(key)
        return key != keys[-1]

    def mock_get_fuel_raster_key(_, version):
        return f"raster_v{version}"

    s3_client = S3Client()
    raster_addresser = RasterKeyAddresser()

    monkeypatch.setattr(s3_client, "all_objects_exist", mock_all_objects_exist)
    monkeypatch.setattr(raster_addresser, "get_fuel_raster_key", mock_get_fuel_raster_key)

    now = datetime(2024, 4, 15)
    result = await find_latest_version(s3_client, raster_addresser, now, 1)

    assert result == len(keys)
    assert call_log == keys


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

    raster_addresser = RasterKeyAddresser()
    monkeypatch.setattr(
        raster_addresser, "get_unprocessed_fuel_raster_key", mock_get_unprocessed_key
    )
    monkeypatch.setattr(raster_addresser, "get_fuel_raster_key", mock_get_fuel_key)

    monkeypatch.setattr("wps_jobs.fuel_raster.S3Client", lambda: MockS3Client())

    async def mock_find_latest_version(_, __, ___, ____):
        return 2

    monkeypatch.setattr("wps_jobs.fuel_raster.find_latest_version", mock_find_latest_version)

    monkeypatch.setattr(
        "wps_jobs.fuel_raster.WPSDataset.from_bytes", lambda res: MockRasterContext()
    )

    mock_db = MockDB()
    monkeypatch.setattr(
        "wps_jobs.fuel_raster.get_async_write_session_scope", lambda: mock_db.MockDBScope(mock_db)
    )

    # UTC now
    monkeypatch.setattr("wps_jobs.fuel_raster.get_utc_now", lambda: datetime(2024, 4, 15, 12, 0))
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

    class MockS3ClientFail(MockS3Client):
        def __init__(self):
            self.deleted = None

        async def delete_object(self, key):
            self.deleted = key

        async def get_content_hash(self, _):
            return "abc123"

        async def get_fuel_raster(_, __, ___):
            raise ValueError("corrupt file")

    mock_s3 = MockS3ClientFail()
    monkeypatch.setattr("wps_jobs.fuel_raster.S3Client", lambda: mock_s3)

    with pytest.raises(ValueError):
        await start_job(
            raster_addresser=raster_addresser,
            start_datetime=datetime(2024, 1, 1),
            unprocessed_object_name="fuel.tif",
        )
        assert mock_db.added == {}
        assert mock_s3.deleted == "fuel-key-v3"


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
