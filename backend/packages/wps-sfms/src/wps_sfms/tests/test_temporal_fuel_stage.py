"""Tests for the SFMS temporal fuel stage."""

import hashlib
from contextlib import asynccontextmanager
from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from botocore.exceptions import ClientError
from pytest_mock import MockerFixture
from wps_shared.db.models.sfms_run import SFMSRunLogJobName
from wps_shared.db.models.temporal_fuel_raster import TemporalFuelRaster

from wps_sfms.run_context import SFMSRunContext
from wps_sfms.temporal_fuel_stage import resolve_temporal_fuel
from wps_sfms.tests.run_test_utils import (
    a_run,
)

# manifest keys strip this bucket's GDAL prefix
pytestmark = pytest.mark.usefixtures("some_bucket")


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


def open_julian_dataset(raster_bytes: bytes) -> MagicMock:
    """A WPSDataset.from_bytes stand-in, named for the bytes it was opened from."""
    dataset = MagicMock(name=raster_bytes.decode())
    dataset.__enter__.return_value = dataset
    return dataset


@pytest.fixture
def temporal_fuel_deps(mocker: MockerFixture, tracked_jobs):
    """Dependencies for the temporal fuel stage, with every Julian raster present."""
    session = MagicMock()

    @asynccontextmanager
    async def _write_scope():
        yield session

    mocker.patch("wps_sfms.temporal_fuel_stage.get_async_write_session_scope", _write_scope)

    addresser = MagicMock()
    addresser.gdal_path.side_effect = lambda key: f"/vsis3/some bucket/{key}"
    addresser.get_julian_key.side_effect = lambda name: name
    addresser.get_temporal_fuel_key.side_effect = lambda _date, version: f"temporal/{version}.tif"
    addresser.get_julian_archive_key.side_effect = lambda name, julian_hash: (
        f"archive/{name}/{julian_hash}.tif"
    )

    s3_client = MagicMock()
    s3_client.all_objects_exist = AsyncMock(return_value=True)
    s3_client.get_fuel_raster = AsyncMock(return_value=b"stored tif")
    s3_client.read_object = AsyncMock(side_effect=lambda key: JULIAN_BYTES[key])
    # no Julian archives yet
    s3_client.object_exists = AsyncMock(return_value=False)
    s3_client.put_object = AsyncMock()
    mocker.patch("wps_sfms.julian_rasters.WPSDataset.from_bytes", side_effect=open_julian_dataset)

    return SimpleNamespace(
        tracked_jobs=tracked_jobs,
        session=session,
        addresser=addresser,
        s3_client=s3_client,
        fuel_type_raster=MagicMock(id=7, object_store_path="sfms/static/fuel/fbp2026_v1.tif"),
        lock=mocker.patch(
            "wps_sfms.temporal_fuel_stage.lock_temporal_fuel_raster_date", new_callable=AsyncMock
        ),
        publish=mocker.patch(
            "wps_sfms.temporal_fuel_stage.publish_temporal_fuel_raster",
            new_callable=AsyncMock,
            return_value="temporal-hash",
        ),
    )


def patch_db(mocker: MockerFixture, existing=None, latest_version: int = 0) -> AsyncMock:
    """Patch the temporal fuel queries; return the mocked reuse lookup."""
    mocker.patch(
        "wps_sfms.temporal_fuel_stage.get_latest_temporal_fuel_raster_version",
        new_callable=AsyncMock,
        return_value=latest_version,
    )
    # autospec so the reuse query's hash kwargs must match the real function's parameters
    return mocker.patch(
        "wps_sfms.temporal_fuel_stage.get_matching_temporal_fuel_raster",
        autospec=True,
        return_value=existing,
    )


def stored_raster(version: int) -> MagicMock:
    """A temporal_fuel_raster row for ``version`` with a recorded content hash."""
    return MagicMock(
        object_store_path=f"temporal/{version}.tif",
        content_hash="stored-hash",
    )


async def resolve(deps) -> tuple[str, SFMSRunContext]:
    """Run the temporal fuel stage for the target date; return its grid path and the run."""
    run = a_run(
        TARGET_DATE,
        addresser=deps.addresser,
        s3_client=deps.s3_client,
        fuel_type_raster=deps.fuel_type_raster,
    )
    return await resolve_temporal_fuel(run), run


def julian_archive_keys() -> dict[str, str]:
    """The archive keys the test fixture's addresser builds for the read Julian rasters."""
    return {name: f"archive/{name}/{JULIAN_HASHES[f'{name}_hash']}.tif" for name in JULIAN_BYTES}


@pytest.mark.anyio
async def test_temporal_fuel_stage_reuses_matching_raster(
    mocker: MockerFixture, temporal_fuel_deps
):
    deps = temporal_fuel_deps
    get_existing = patch_db(mocker, existing=stored_raster(version=2))
    deps.s3_client.object_exists.return_value = True

    path, run = await resolve(deps)

    assert path == "/vsis3/some bucket/temporal/2.tif"
    assert deps.tracked_jobs == [SFMSRunLogJobName.TEMPORAL_FUEL]
    # the grid is an FBP input and an output, and the reused grid's Julian inputs are traced by
    # archive key, so they survive the live Julian keys being replaced
    assert run.manifest.input.fuel_raster.temporal == "temporal/2.tif"
    assert run.manifest.output.fuel_raster == "temporal/2.tif"
    assert run.manifest.input.julian_rasters == julian_archive_keys()
    deps.lock.assert_awaited_once_with(deps.session, TARGET_DATE)
    get_existing.assert_awaited_once_with(deps.session, TARGET_DATE, 7, **JULIAN_HASHES)
    deps.s3_client.get_fuel_raster.assert_awaited_once_with("temporal/2.tif", "stored-hash")
    deps.publish.assert_not_awaited()
    deps.s3_client.put_object.assert_not_awaited()
    deps.session.add.assert_not_called()


@pytest.mark.anyio
async def test_temporal_fuel_stage_restores_only_missing_archives(
    mocker: MockerFixture, temporal_fuel_deps
):
    deps = temporal_fuel_deps
    patch_db(mocker, existing=stored_raster(version=2))
    missing_key = f"archive/grass_matted/{JULIAN_HASHES['grass_matted_hash']}.tif"
    deps.s3_client.object_exists.side_effect = lambda key: key != missing_key

    await resolve(deps)

    # a reused grid still gets its missing archive back, and existing archives aren't rewritten
    deps.publish.assert_not_awaited()
    deps.s3_client.put_object.assert_awaited_once_with(missing_key, JULIAN_BYTES["grass_matted"])


@pytest.mark.anyio
async def test_temporal_fuel_stage_records_next_version(mocker: MockerFixture, temporal_fuel_deps):
    deps = temporal_fuel_deps
    patch_db(mocker, existing=None, latest_version=2)

    path, run = await resolve(deps)

    assert path == "/vsis3/some bucket/temporal/3.tif"
    assert run.manifest.input.julian_rasters == julian_archive_keys()
    publish_args = deps.publish.await_args.kwargs
    assert publish_args["base_fuel_key"] == "/vsis3/some bucket/sfms/static/fuel/fbp2026_v1.tif"
    # the grid is built from the same bytes that were hashed, and each dataset is closed after
    for name, raster_bytes in JULIAN_BYTES.items():
        dataset = getattr(publish_args["julian"], name)
        assert dataset._mock_name == raster_bytes.decode()
        dataset.__exit__.assert_called_once()

    record: TemporalFuelRaster = deps.session.add.call_args.args[0]
    assert record.fuel_type_raster_id == 7
    assert record.for_date == TARGET_DATE
    assert record.version == 3
    assert record.object_store_path == "temporal/3.tif"
    assert record.content_hash == "temporal-hash"
    for column, julian_hash in JULIAN_HASHES.items():
        assert getattr(record, column) == julian_hash

    # the exact Julian bytes that were hashed are archived under their hash and recorded
    archived = {call.args[0]: call.args[1] for call in deps.s3_client.put_object.await_args_list}
    for name, raster_bytes in JULIAN_BYTES.items():
        archive_key = f"archive/{name}/{JULIAN_HASHES[f'{name}_hash']}.tif"
        assert archived[archive_key] == raster_bytes
        assert getattr(record, f"{name}_archive_path") == archive_key


@pytest.mark.anyio
@pytest.mark.parametrize(
    "stored_raster_error",
    [
        ValueError("Content hash does not match expected hash"),
        ClientError({"Error": {"Code": "NoSuchKey"}}, "GetObject"),
    ],
    ids=["altered", "missing"],
)
async def test_temporal_fuel_stage_rebuilds_unverified_raster(
    mocker: MockerFixture, temporal_fuel_deps, stored_raster_error: Exception
):
    deps = temporal_fuel_deps
    patch_db(mocker, existing=stored_raster(version=2), latest_version=2)
    deps.s3_client.get_fuel_raster.side_effect = stored_raster_error

    path, _run = await resolve(deps)

    assert path == "/vsis3/some bucket/temporal/3.tif"
    deps.publish.assert_awaited_once()
    assert deps.session.add.call_args.args[0].version == 3


@pytest.mark.anyio
async def test_temporal_fuel_stage_raises_unexpected_storage_errors(
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
async def test_temporal_fuel_stage_requires_julian_rasters(temporal_fuel_deps):
    deps = temporal_fuel_deps
    deps.s3_client.all_objects_exist.return_value = False

    with pytest.raises(RuntimeError, match="Missing Julian date rasters"):
        await resolve(deps)

    deps.s3_client.all_objects_exist.assert_awaited_once_with(
        "green_up_on", "green_up_off", "grass_standing", "grass_matted"
    )
    deps.s3_client.read_object.assert_not_awaited()
