import hashlib
from contextlib import asynccontextmanager
from datetime import date, datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from botocore.exceptions import ClientError
from pytest_mock import MockerFixture
from wps_shared.db.models.sfms_run import SFMSRunLogJobName
from wps_shared.db.models.temporal_fuel_raster import TemporalFuelRaster
from wps_shared.run_type import RunType

from app.jobs.sfms_run_pipeline import (
    _resolve_percent_conifer_path,
    _resolve_percent_dead_conifer_path,
    TemporalFuelPaths,
    resolve_temporal_fuel_raster,
    run_temporal_fuel,
    run_fbp_calculations,
)

PIPELINE_PATH = "app.jobs.sfms_run_pipeline"


@pytest.mark.anyio
async def test_resolve_percent_conifer_path_uses_fuel_raster_year():
    addresser = MagicMock()
    addresser.get_percent_conifer_key.side_effect = lambda year: f"sfms/static/m12_{year}.tif"
    addresser.gdal_path.side_effect = lambda key: f"/vsis3/test/{key}"
    s3_client = MagicMock()
    s3_client.object_exists = AsyncMock(return_value=True)

    result = await _resolve_percent_conifer_path(2025, addresser, s3_client)

    assert result == "/vsis3/test/sfms/static/m12_2025.tif"
    s3_client.object_exists.assert_awaited_once_with("sfms/static/m12_2025.tif")


@pytest.mark.anyio
async def test_resolve_percent_conifer_path_does_not_fall_back_one_year():
    addresser = MagicMock()
    addresser.get_percent_conifer_key.side_effect = lambda year: f"sfms/static/m12_{year}.tif"
    s3_client = MagicMock()
    s3_client.object_exists = AsyncMock(side_effect=[False, True])

    with pytest.raises(
        RuntimeError,
        match="fuel-grid year 2025: sfms/static/m12_2025.tif",
    ):
        await _resolve_percent_conifer_path(2025, addresser, s3_client)

    addresser.get_percent_conifer_key.assert_called_once_with(2025)
    s3_client.object_exists.assert_awaited_once_with("sfms/static/m12_2025.tif")
    addresser.gdal_path.assert_not_called()


@pytest.mark.anyio
async def test_resolve_percent_dead_conifer_path_uses_fuel_raster_year():
    addresser = MagicMock()
    addresser.get_percent_dead_conifer_key.side_effect = lambda year: f"sfms/static/m34_{year}.tif"
    addresser.gdal_path.side_effect = lambda key: f"/vsis3/test/{key}"
    s3_client = MagicMock()
    s3_client.object_exists = AsyncMock(return_value=True)

    result = await _resolve_percent_dead_conifer_path(2025, addresser, s3_client)

    assert result == "/vsis3/test/sfms/static/m34_2025.tif"
    s3_client.object_exists.assert_awaited_once_with("sfms/static/m34_2025.tif")


@pytest.mark.anyio
async def test_resolve_percent_dead_conifer_path_raises_when_missing():
    addresser = MagicMock()
    addresser.get_percent_dead_conifer_key.side_effect = lambda year: f"sfms/static/m34_{year}.tif"
    s3_client = MagicMock()
    s3_client.object_exists = AsyncMock(return_value=False)

    with pytest.raises(
        RuntimeError,
        match="fuel-grid year 2025: sfms/static/m34_2025.tif",
    ):
        await _resolve_percent_dead_conifer_path(2025, addresser, s3_client)

    addresser.get_percent_dead_conifer_key.assert_called_once_with(2025)
    s3_client.object_exists.assert_awaited_once_with("sfms/static/m34_2025.tif")
    addresser.gdal_path.assert_not_called()


@pytest.mark.anyio
async def test_run_fbp_calculations_runs_one_tracked_primary_calculation(
    mocker: MockerFixture,
):
    datetime_to_process = datetime(2025, 7, 4, 20, tzinfo=timezone.utc)
    addresser = MagicMock()
    s3_client = MagicMock()
    session = MagicMock()
    primary_inputs = MagicMock()
    addresser.get_primary_fire_behaviour_inputs.return_value = primary_inputs
    resolve_percent_conifer = mocker.patch(
        f"{PIPELINE_PATH}._resolve_percent_conifer_path",
        new=AsyncMock(return_value="/vsis3/test/sfms/static/m12_2025.tif"),
    )
    primary_processor = MagicMock()
    primary_processor.process = AsyncMock()
    primary_processor_class = mocker.patch(
        f"{PIPELINE_PATH}.PrimaryFireBehaviourProcessor", return_value=primary_processor
    )
    tracked_jobs = []

    async def run_tracked_job(job_name, _sfms_run_id, _session, action):
        tracked_jobs.append(job_name)
        await action()

    mocker.patch(f"{PIPELINE_PATH}._run_tracked_job", side_effect=run_tracked_job)

    await run_fbp_calculations(
        datetime_to_process,
        addresser,
        s3_client,
        TemporalFuelPaths(
            raster_path="/vsis3/test/fuel.tif", fuel_codes_lookup_key="test/fuel.json"
        ),
        2025,
        42,
        session,
        RunType.ACTUAL,
    )

    resolve_percent_conifer.assert_awaited_once_with(2025, addresser, s3_client)
    addresser.get_primary_fire_behaviour_inputs.assert_called_once_with(
        datetime_to_process,
        RunType.ACTUAL,
        "/vsis3/test/fuel.tif",
        "test/fuel.json",
        "/vsis3/test/sfms/static/m12_2025.tif",
        addresser.gdal_path.return_value,
        addresser.gdal_path.return_value,
        addresser.gdal_path.return_value,
        addresser.gdal_path.return_value,
        addresser.gdal_path.return_value,
    )
    primary_processor_class.assert_called_once_with(datetime_to_process)
    primary_processor.process.assert_awaited_once()
    assert primary_processor.process.await_args.args[0] is s3_client
    assert primary_processor.process.await_args.args[2] is primary_inputs
    assert tracked_jobs == [SFMSRunLogJobName.PRIMARY_FBP_CALCULATION]


TARGET_DATE = date(2026, 6, 1)
# each Julian key is named after its hash column, e.g. "green_up_on" -> "green_up_on_hash"
JULIAN_BYTES = {
    "green_up_on": b"on tif",
    "green_up_off": b"off tif",
    "grass_standing": b"standing tif",
    "grass_matted": b"matted tif",
}
JULIAN_HASHES = {
    f"{key}_hash": hashlib.sha256(raster_bytes).hexdigest()
    for key, raster_bytes in JULIAN_BYTES.items()
}
STORED_LOOKUP = b'{"fuel_codes": []}'


def read_stored_object(lookup: bytes | Exception = STORED_LOOKUP):
    """A read_object stand-in serving the Julian rasters and ``lookup`` for any other key."""

    async def _read_object(key: str) -> bytes:
        if key in JULIAN_BYTES:
            return JULIAN_BYTES[key]
        if isinstance(lookup, Exception):
            raise lookup
        return lookup

    return AsyncMock(side_effect=_read_object)


def open_julian_dataset(raster_bytes: bytes) -> MagicMock:
    """A WPSDataset.from_bytes stand-in, named for the bytes it was opened from."""
    dataset = MagicMock(name=raster_bytes.decode())
    dataset.__enter__.return_value = dataset
    return dataset


@pytest.fixture
def temporal_fuel_deps(mocker: MockerFixture):
    """Dependencies for resolve_temporal_fuel_raster, with every Julian raster present."""
    session = MagicMock()

    @asynccontextmanager
    async def _write_scope():
        yield session

    mocker.patch(f"{PIPELINE_PATH}.get_async_write_session_scope", _write_scope)

    addresser = MagicMock()
    addresser.gdal_path.side_effect = lambda key: f"/vsis3/bucket/{key}"
    addresser.get_green_up_on_key.return_value = "green_up_on"
    addresser.get_green_up_off_key.return_value = "green_up_off"
    addresser.get_grass_standing_key.return_value = "grass_standing"
    addresser.get_grass_matted_key.return_value = "grass_matted"
    addresser.get_temporal_fuel_key.side_effect = lambda _date, version: f"temporal/{version}.tif"
    addresser.get_fuel_codes_lookup_key.side_effect = lambda _date, version: (
        f"temporal/{version}.json"
    )

    s3_client = MagicMock()
    s3_client.all_objects_exist = AsyncMock(return_value=True)
    s3_client.get_fuel_raster = AsyncMock(return_value=b"stored tif")
    s3_client.read_object = read_stored_object()
    mocker.patch(f"{PIPELINE_PATH}.WPSDataset.from_bytes", side_effect=open_julian_dataset)

    return SimpleNamespace(
        session=session,
        addresser=addresser,
        s3_client=s3_client,
        fuel_type_raster=MagicMock(id=7, object_store_path="sfms/static/fuel/fbp2026_v1.tif"),
        lock=mocker.patch(
            f"{PIPELINE_PATH}.lock_temporal_fuel_raster_date", new_callable=AsyncMock
        ),
        publish=mocker.patch(
            f"{PIPELINE_PATH}.publish_temporal_fuel_raster",
            new_callable=AsyncMock,
            return_value="temporal-hash",
        ),
    )


def patch_db(mocker: MockerFixture, existing=None, latest_version: int = 0) -> AsyncMock:
    """Patch the temporal fuel queries; return the mocked reuse lookup."""
    mocker.patch(
        f"{PIPELINE_PATH}.get_latest_temporal_fuel_raster_version",
        new_callable=AsyncMock,
        return_value=latest_version,
    )
    return mocker.patch(
        f"{PIPELINE_PATH}.get_matching_temporal_fuel_raster",
        new_callable=AsyncMock,
        return_value=existing,
    )


def stored_raster(version: int) -> MagicMock:
    """A temporal_fuel_raster row for ``version`` with a recorded content hash."""
    return MagicMock(
        object_store_path=f"temporal/{version}.tif",
        fuel_codes_lookup_path=f"temporal/{version}.json",
        content_hash="stored-hash",
    )


async def resolve(deps) -> TemporalFuelPaths:
    return await resolve_temporal_fuel_raster(
        TARGET_DATE, deps.fuel_type_raster, deps.addresser, deps.s3_client
    )


@pytest.mark.anyio
async def test_resolve_temporal_fuel_raster_reuses_matching_raster(
    mocker: MockerFixture, temporal_fuel_deps
):
    deps = temporal_fuel_deps
    get_existing = patch_db(mocker, existing=stored_raster(version=2))

    result = await resolve(deps)

    assert result == TemporalFuelPaths(
        raster_path="/vsis3/bucket/temporal/2.tif", fuel_codes_lookup_key="temporal/2.json"
    )
    deps.lock.assert_awaited_once_with(deps.session, TARGET_DATE)
    get_existing.assert_awaited_once_with(deps.session, TARGET_DATE, 7, **JULIAN_HASHES)
    deps.s3_client.get_fuel_raster.assert_awaited_once_with("temporal/2.tif", "stored-hash")
    deps.publish.assert_not_awaited()
    deps.session.add.assert_not_called()


@pytest.mark.anyio
async def test_resolve_temporal_fuel_raster_records_next_version(
    mocker: MockerFixture, temporal_fuel_deps
):
    deps = temporal_fuel_deps
    patch_db(mocker, existing=None, latest_version=2)

    result = await resolve(deps)

    assert result == TemporalFuelPaths(
        raster_path="/vsis3/bucket/temporal/3.tif", fuel_codes_lookup_key="temporal/3.json"
    )
    publish_args = deps.publish.await_args.kwargs
    assert publish_args["base_fuel_key"] == "/vsis3/bucket/sfms/static/fuel/fbp2026_v1.tif"
    # the grid is built from the same bytes that were hashed, and each dataset is closed after
    for name, raster_bytes in JULIAN_BYTES.items():
        dataset = publish_args[name]
        assert dataset._mock_name == raster_bytes.decode()
        dataset.__exit__.assert_called_once()

    record: TemporalFuelRaster = deps.session.add.call_args.args[0]
    assert record.fuel_type_raster_id == 7
    assert record.for_date == TARGET_DATE
    assert record.version == 3
    assert record.object_store_path == "temporal/3.tif"
    assert record.fuel_codes_lookup_path == "temporal/3.json"
    assert record.content_hash == "temporal-hash"
    for column, julian_hash in JULIAN_HASHES.items():
        assert getattr(record, column) == julian_hash


@pytest.mark.anyio
@pytest.mark.parametrize(
    "stored_raster_error",
    [
        ValueError("Content hash does not match expected hash"),
        ClientError({"Error": {"Code": "NoSuchKey"}}, "GetObject"),
    ],
    ids=["altered", "missing"],
)
async def test_resolve_temporal_fuel_raster_rebuilds_unverified_raster(
    mocker: MockerFixture, temporal_fuel_deps, stored_raster_error: Exception
):
    deps = temporal_fuel_deps
    patch_db(mocker, existing=stored_raster(version=2), latest_version=2)
    deps.s3_client.get_fuel_raster.side_effect = stored_raster_error

    result = await resolve(deps)

    assert result.raster_path == "/vsis3/bucket/temporal/3.tif"
    deps.publish.assert_awaited_once()
    assert deps.session.add.call_args.args[0].version == 3


@pytest.mark.anyio
@pytest.mark.parametrize(
    "stored_lookup",
    [ClientError({"Error": {"Code": "NoSuchKey"}}, "GetObject"), b"not json"],
    ids=["missing", "unparseable"],
)
async def test_resolve_temporal_fuel_raster_rebuilds_unverified_lookup(
    mocker: MockerFixture, temporal_fuel_deps, stored_lookup: bytes | Exception
):
    deps = temporal_fuel_deps
    patch_db(mocker, existing=stored_raster(version=2), latest_version=2)
    deps.s3_client.read_object = read_stored_object(stored_lookup)

    result = await resolve(deps)

    assert result.fuel_codes_lookup_key == "temporal/3.json"
    deps.publish.assert_awaited_once()
    assert deps.session.add.call_args.args[0].version == 3


@pytest.mark.anyio
async def test_resolve_temporal_fuel_raster_raises_unexpected_storage_errors(
    mocker: MockerFixture, temporal_fuel_deps
):
    deps = temporal_fuel_deps
    patch_db(mocker, existing=stored_raster(version=2))
    deps.s3_client.get_fuel_raster.side_effect = ClientError(
        {"Error": {"Code": "AccessDenied"}}, "GetObject"
    )

    with pytest.raises(ClientError, match="AccessDenied"):
        await resolve(deps)

    deps.publish.assert_not_awaited()


@pytest.mark.anyio
async def test_resolve_temporal_fuel_raster_requires_julian_rasters(temporal_fuel_deps):
    deps = temporal_fuel_deps
    deps.s3_client.all_objects_exist.return_value = False

    with pytest.raises(RuntimeError, match="Missing Julian date rasters"):
        await resolve(deps)

    deps.s3_client.all_objects_exist.assert_awaited_once_with(
        "green_up_on", "green_up_off", "grass_standing", "grass_matted"
    )
    deps.s3_client.read_object.assert_not_awaited()


@pytest.mark.anyio
async def test_run_temporal_fuel_is_a_tracked_job_for_the_date(mocker: MockerFixture):
    temporal_fuel = TemporalFuelPaths(raster_path="/vsis3/t.tif", fuel_codes_lookup_key="t.json")
    resolve = mocker.patch(
        f"{PIPELINE_PATH}.resolve_temporal_fuel_raster",
        new_callable=AsyncMock,
        return_value=temporal_fuel,
    )
    tracked_jobs = []

    async def run_tracked_job(job_name, sfms_run_id, _session, action):
        tracked_jobs.append((job_name, sfms_run_id))
        return await action()

    mocker.patch(f"{PIPELINE_PATH}._run_tracked_job", side_effect=run_tracked_job)
    fuel_type_raster, addresser, s3_client = MagicMock(), MagicMock(), MagicMock()

    result = await run_temporal_fuel(
        datetime(2026, 6, 1, 20, tzinfo=timezone.utc),
        fuel_type_raster,
        addresser,
        s3_client,
        42,
        MagicMock(),
    )

    assert result == temporal_fuel
    assert tracked_jobs == [(SFMSRunLogJobName.TEMPORAL_FUEL, 42)]
    resolve.assert_awaited_once_with(TARGET_DATE, fuel_type_raster, addresser, s3_client)
