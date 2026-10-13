import hashlib
from dataclasses import fields
from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest_mock import MockerFixture
from wps_shared.db.models.temporal_fuel_raster import TemporalFuelRaster

from wps_sfms.julian_rasters import JulianRasters, read_julian_rasters
from wps_sfms.sfmsng_raster_addresser import SFMSNGRasterAddresser

# every raster gets distinct bytes, so pairing a name with another raster's data fails a test
NAMES = [field.name for field in fields(JulianRasters)]
RASTER_BYTES = {name: f"{name} tif".encode() for name in NAMES}
HASHES = {
    name: hashlib.sha256(raster_bytes).hexdigest() for name, raster_bytes in RASTER_BYTES.items()
}


@pytest.fixture
def addresser() -> SFMSNGRasterAddresser:
    return SFMSNGRasterAddresser()


@pytest.fixture
def s3_client(addresser: SFMSNGRasterAddresser) -> MagicMock:
    """Serves each Julian raster's own bytes from its live key."""
    bytes_by_key = {addresser.get_julian_key(name): RASTER_BYTES[name] for name in NAMES}
    client = MagicMock()
    client.all_objects_exist = AsyncMock(return_value=True)
    client.read_object = AsyncMock(side_effect=lambda key: bytes_by_key[key])
    return client


@pytest.fixture
async def julian(s3_client: MagicMock, addresser: SFMSNGRasterAddresser) -> JulianRasters:
    return await read_julian_rasters(s3_client, addresser)


@pytest.mark.anyio
async def test_read_julian_rasters_pairs_each_name_with_its_own_raster(
    julian: JulianRasters, addresser: SFMSNGRasterAddresser
):
    for name in NAMES:
        raster = getattr(julian, name)
        assert raster.name == name
        assert raster.raster_bytes == RASTER_BYTES[name]
        assert raster.content_hash == HASHES[name]
        assert raster.archive_key == addresser.get_julian_archive_key(name, HASHES[name])


@pytest.mark.anyio
async def test_read_julian_rasters_raises_when_a_raster_is_missing(
    s3_client: MagicMock, addresser: SFMSNGRasterAddresser
):
    s3_client.all_objects_exist.return_value = False

    with pytest.raises(RuntimeError, match="Missing Julian date rasters"):
        await read_julian_rasters(s3_client, addresser)

    s3_client.read_object.assert_not_awaited()


@pytest.mark.anyio
async def test_column_methods_map_each_column_to_its_own_raster(
    julian: JulianRasters, addresser: SFMSNGRasterAddresser
):
    assert julian.hash_columns() == {
        TemporalFuelRaster.green_up_on_hash.key: HASHES["green_up_on"],
        TemporalFuelRaster.green_up_off_hash.key: HASHES["green_up_off"],
        TemporalFuelRaster.grass_standing_hash.key: HASHES["grass_standing"],
        TemporalFuelRaster.grass_matted_hash.key: HASHES["grass_matted"],
    }
    assert julian.archive_path_columns() == {
        TemporalFuelRaster.green_up_on_archive_path.key: addresser.get_julian_archive_key(
            "green_up_on", HASHES["green_up_on"]
        ),
        TemporalFuelRaster.green_up_off_archive_path.key: addresser.get_julian_archive_key(
            "green_up_off", HASHES["green_up_off"]
        ),
        TemporalFuelRaster.grass_standing_archive_path.key: addresser.get_julian_archive_key(
            "grass_standing", HASHES["grass_standing"]
        ),
        TemporalFuelRaster.grass_matted_archive_path.key: addresser.get_julian_archive_key(
            "grass_matted", HASHES["grass_matted"]
        ),
    }


@pytest.mark.anyio
async def test_as_datasets_opens_each_dataset_from_its_own_bytes(
    mocker: MockerFixture, julian: JulianRasters
):
    def open_dataset(raster_bytes: bytes) -> MagicMock:
        dataset = MagicMock(name=raster_bytes.decode())
        dataset.__enter__.return_value = dataset
        return dataset

    mocker.patch("wps_sfms.julian_rasters.WPSDataset.from_bytes", side_effect=open_dataset)

    with julian.as_datasets() as datasets:
        opened = {name: getattr(datasets, name) for name in NAMES}
        for name, dataset in opened.items():
            assert dataset._mock_name == RASTER_BYTES[name].decode()
            dataset.__exit__.assert_not_called()

    for dataset in opened.values():
        dataset.__exit__.assert_called_once()
