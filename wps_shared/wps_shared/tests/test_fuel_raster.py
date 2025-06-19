from datetime import datetime

import pytest

from wps_shared.fuel_raster import find_latest_version, process_fuel_type_raster
from wps_shared.sfms.raster_addresser import RasterKeyAddresser
from wps_shared.utils.s3_client import S3Client

CREATE_TIMESTAMP = datetime(2024, 4, 15, 12, 0)


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

    monkeypatch.setattr("wps_shared.fuel_raster.S3Client", lambda: MockS3Client())

    async def mock_find_latest_version(_, __, ___, ____):
        return 2

    monkeypatch.setattr("wps_shared.fuel_raster.find_latest_version", mock_find_latest_version)

    monkeypatch.setattr(
        "wps_shared.fuel_raster.WPSDataset.from_bytes", lambda res: MockRasterContext()
    )

    # UTC now
    monkeypatch.setattr("wps_shared.fuel_raster.get_utc_now", lambda: CREATE_TIMESTAMP)
    return raster_addresser


@pytest.mark.anyio
async def test_process_fuel_type_raster_success(monkeypatch):
    start_datetime = datetime(2024, 1, 1)
    raster_addresser = setup_mocks(monkeypatch)

    (
        year,
        version,
        xsize,
        ysize,
        object_store_path,
        content_hash,
        create_timestamp,
    ) = await process_fuel_type_raster(
        raster_addresser=raster_addresser,
        start_datetime=start_datetime,
        unprocessed_object_name="fuel.tif",
    )

    assert year == start_datetime.year
    assert version == 3
    assert xsize == 100
    assert ysize == 200
    assert object_store_path == "fuel-key-v3"
    assert content_hash == "abc123"
    assert create_timestamp == CREATE_TIMESTAMP


@pytest.mark.anyio
async def test_process_fuel_type_raster_failure(monkeypatch):
    raster_addresser = setup_mocks(monkeypatch)

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
    monkeypatch.setattr("wps_shared.fuel_raster.S3Client", lambda: mock_s3)

    with pytest.raises(ValueError):
        await process_fuel_type_raster(
            raster_addresser=raster_addresser,
            start_datetime=datetime(2024, 1, 1),
            unprocessed_object_name="fuel.tif",
        )
