import hashlib
from contextlib import asynccontextmanager
from datetime import date, datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from botocore.exceptions import ClientError
from pytest_mock import MockerFixture
from wps_sfms.processors.idw import RasterProcessor
from wps_sfms.raster_inputs import FWIInputs
from wps_sfms.run_manifest import SFMSRunManifest
from wps_shared.db.models.sfms_run import SFMSRunLogJobName
from wps_shared.db.models.temporal_fuel_raster import TemporalFuelRaster
from wps_shared.run_type import RunType
from wps_shared.sfms.raster_addresser import FBPParameter

from app.jobs.sfms_run_pipeline import (
    ResolvedTemporalFuelRaster,
    SFMSRunContext,
    _resolve_percent_conifer_path,
    _resolve_percent_dead_conifer_path,
    resolve_temporal_fuel_raster,
    run_fbp_calculations,
    run_fwi_calculations,
    run_temporal_fuel,
    run_weather_interpolation,
)
from app.tests.conftest import create_mock_sfms_actuals

PIPELINE_PATH = "app.jobs.sfms_run_pipeline"

RUN_DATETIME = datetime(2025, 7, 4, 20, 45, tzinfo=timezone.utc)


def datetime_to_process_for(for_date: date) -> datetime:
    """The hour-20 UTC datetime a target date is processed at."""
    return datetime(for_date.year, for_date.month, for_date.day, 20, tzinfo=timezone.utc)


def a_run(
    for_date: date = date(2025, 7, 4),
    run_type: RunType = RunType.ACTUAL,
    sfms_run_id: int = 42,
    addresser: MagicMock | None = None,
    s3_client: MagicMock | None = None,
    session: MagicMock | None = None,
) -> SFMSRunContext:
    """A run context for one target date, tracing into a real manifest."""
    return SFMSRunContext.start(
        datetime_to_process_for(for_date),
        run_type,
        sfms_run_id,
        RUN_DATETIME,
        session or MagicMock(),
        s3_client or MagicMock(),
        addresser or MagicMock(),
    )


async def _run_action(job_name, _sfms_run_id, _session, action):
    """A _run_tracked_job stand-in that runs the job without the run log."""
    await action()


class TestSFMSRunContext:
    """The run context keeps a manifest describing the run it's started for."""

    def test_start_creates_a_manifest_describing_the_run(self):
        run = a_run(date(2026, 6, 1), RunType.FORECAST)

        assert run.datetime_to_process == datetime(2026, 6, 1, 20, tzinfo=timezone.utc)
        assert run.run_type == RunType.FORECAST
        assert run.sfms_run_id == 42
        assert run.manifest.run_type == RunType.FORECAST
        assert run.manifest.for_date == date(2026, 6, 1)
        assert run.manifest.run_datetime == RUN_DATETIME

    @pytest.mark.parametrize(
        "manifest",
        [
            SFMSRunManifest(
                run_type=RunType.FORECAST,
                for_date=date(2025, 7, 4),
                run_datetime=RUN_DATETIME,
            ),
            SFMSRunManifest(
                run_type=RunType.ACTUAL, for_date=date(2025, 7, 5), run_datetime=RUN_DATETIME
            ),
        ],
        ids=["another run type", "another target date"],
    )
    def test_rejects_a_manifest_describing_another_run(self, manifest: SFMSRunManifest):
        with pytest.raises(AssertionError, match="the manifest must describe"):
            SFMSRunContext(
                datetime_to_process_for(date(2025, 7, 4)),
                RunType.ACTUAL,
                42,
                manifest,
                MagicMock(),
                MagicMock(),
                MagicMock(),
            )


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
    addresser.get_slope_key.side_effect = lambda: "sfms_ng/static/bc_slope.tif"
    addresser.get_aspect_key.side_effect = lambda: "sfms_ng/static/bc_aspect.tif"
    addresser.gdal_path.side_effect = lambda key: f"/vsis3/some bucket/{key}"
    s3_client = MagicMock()
    session = MagicMock()
    fbp_output_keys = {
        parameter: f"sfms_ng/actual/2025/07/04/{parameter.value}_20250704.tif"
        for parameter in FBPParameter
    }
    primary_inputs = MagicMock()
    primary_inputs.output_keys = fbp_output_keys
    addresser.get_primary_fire_behaviour_inputs.return_value = primary_inputs
    resolve_percent_conifer = mocker.patch(
        f"{PIPELINE_PATH}._resolve_percent_conifer_path",
        new=AsyncMock(return_value="/vsis3/some bucket/sfms/static/m12_2025.tif"),
    )
    primary_processor = MagicMock()
    primary_processor.process = AsyncMock()
    primary_processor_class = mocker.patch(
        f"{PIPELINE_PATH}.PrimaryFireBehaviourProcessor", return_value=primary_processor
    )
    tracked_jobs = []

    async def run_tracked_job(job_name, _ctx, _session, action):
        tracked_jobs.append(job_name)
        await action()

    mocker.patch(f"{PIPELINE_PATH}._run_tracked_job", side_effect=run_tracked_job)
    run = a_run(addresser=addresser, s3_client=s3_client, session=session)

    await run_fbp_calculations(run, "/vsis3/some bucket/fuel.tif", 2025)

    resolve_percent_conifer.assert_awaited_once_with(2025, addresser, s3_client)
    addresser.get_primary_fire_behaviour_inputs.assert_called_once_with(
        datetime_to_process,
        RunType.ACTUAL,
        "/vsis3/some bucket/fuel.tif",
        "/vsis3/some bucket/sfms/static/m12_2025.tif",
        f"/vsis3/some bucket/{addresser.get_weather_key.return_value}",
        f"/vsis3/some bucket/{addresser.get_weather_key.return_value}",
        f"/vsis3/some bucket/{addresser.get_fmc_key.return_value}",
        "/vsis3/some bucket/sfms_ng/static/bc_slope.tif",
        "/vsis3/some bucket/sfms_ng/static/bc_aspect.tif",
    )
    primary_processor_class.assert_called_once_with(datetime_to_process)
    primary_processor.process.assert_awaited_once()
    assert primary_processor.process.await_args.args[0] is s3_client
    assert primary_processor.process.await_args.args[2] is primary_inputs
    assert tracked_jobs == [SFMSRunLogJobName.PRIMARY_FBP_CALCULATION]

    # the manifest records the percent-conifer and terrain rasters FBP read, and its outputs
    assert run.manifest.input.fuel_raster.pc == "sfms/static/m12_2025.tif"
    assert run.manifest.input.static_rasters == {
        "slope": "sfms_ng/static/bc_slope.tif",
        "aspect": "sfms_ng/static/bc_aspect.tif",
    }
    assert run.manifest.output.fbp == {
        parameter.value: key for parameter, key in fbp_output_keys.items()
    }


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
def temporal_fuel_deps(mocker: MockerFixture):
    """Dependencies for resolve_temporal_fuel_raster, with every Julian raster present."""
    session = MagicMock()

    @asynccontextmanager
    async def _write_scope():
        yield session

    mocker.patch(f"{PIPELINE_PATH}.get_async_write_session_scope", _write_scope)

    addresser = MagicMock()
    addresser.gdal_path.side_effect = lambda key: f"/vsis3/bucket/{key}"
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
    # autospec so the reuse query's hash kwargs must match the real function's parameters
    return mocker.patch(
        f"{PIPELINE_PATH}.get_matching_temporal_fuel_raster",
        autospec=True,
        return_value=existing,
    )


def stored_raster(version: int) -> MagicMock:
    """A temporal_fuel_raster row for ``version`` with a recorded content hash."""
    return MagicMock(
        object_store_path=f"temporal/{version}.tif",
        content_hash="stored-hash",
    )


async def resolve(deps) -> ResolvedTemporalFuelRaster:
    return await resolve_temporal_fuel_raster(
        TARGET_DATE, deps.fuel_type_raster, deps.addresser, deps.s3_client
    )


def julian_archive_keys() -> dict[str, str]:
    """The archive keys the test fixture's addresser builds for the read Julian rasters."""
    return {name: f"archive/{name}/{JULIAN_HASHES[f'{name}_hash']}.tif" for name in JULIAN_BYTES}


@pytest.mark.anyio
async def test_resolve_temporal_fuel_raster_reuses_matching_raster(
    mocker: MockerFixture, temporal_fuel_deps
):
    deps = temporal_fuel_deps
    get_existing = patch_db(mocker, existing=stored_raster(version=2))
    deps.s3_client.object_exists.return_value = True

    result = await resolve(deps)

    assert result.path == "/vsis3/bucket/temporal/2.tif"
    # the reused grid's inputs survive the live Julian keys being replaced
    assert result.julian_archive_keys == julian_archive_keys()
    deps.lock.assert_awaited_once_with(deps.session, TARGET_DATE)
    get_existing.assert_awaited_once_with(deps.session, TARGET_DATE, 7, **JULIAN_HASHES)
    deps.s3_client.get_fuel_raster.assert_awaited_once_with("temporal/2.tif", "stored-hash")
    deps.publish.assert_not_awaited()
    deps.s3_client.put_object.assert_not_awaited()
    deps.session.add.assert_not_called()


@pytest.mark.anyio
async def test_resolve_temporal_fuel_raster_restores_only_missing_archives(
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
async def test_resolve_temporal_fuel_raster_records_next_version(
    mocker: MockerFixture, temporal_fuel_deps
):
    deps = temporal_fuel_deps
    patch_db(mocker, existing=None, latest_version=2)

    result = await resolve(deps)

    assert result.path == "/vsis3/bucket/temporal/3.tif"
    assert result.julian_archive_keys == julian_archive_keys()
    publish_args = deps.publish.await_args.kwargs
    assert publish_args["base_fuel_key"] == "/vsis3/bucket/sfms/static/fuel/fbp2026_v1.tif"
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
async def test_resolve_temporal_fuel_raster_rebuilds_unverified_raster(
    mocker: MockerFixture, temporal_fuel_deps, stored_raster_error: Exception
):
    deps = temporal_fuel_deps
    patch_db(mocker, existing=stored_raster(version=2), latest_version=2)
    deps.s3_client.get_fuel_raster.side_effect = stored_raster_error

    result = await resolve(deps)

    assert result.path == "/vsis3/bucket/temporal/3.tif"
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
    temporal_fuel = "/vsis3/some bucket/sfms_ng/fuel/temporal/2026/06/01/1/fbp2026_06_01_1.tif"
    julian_archive_keys = {
        "green_up_on": "sfms_ng/static/julian/archive/green_up_on/green-up-hash.tif",
        "green_up_off": "sfms_ng/static/julian/archive/green_up_off/green-off-hash.tif",
        "grass_standing": "sfms_ng/static/julian/archive/grass_standing/standing-hash.tif",
        "grass_matted": "sfms_ng/static/julian/archive/grass_matted/matted-hash.tif",
    }
    resolve = mocker.patch(
        f"{PIPELINE_PATH}.resolve_temporal_fuel_raster",
        new_callable=AsyncMock,
        return_value=ResolvedTemporalFuelRaster(
            path=temporal_fuel, julian_archive_keys=julian_archive_keys
        ),
    )
    tracked_jobs = []

    async def run_tracked_job(job_name, sfms_run_id, _session, action):
        tracked_jobs.append((job_name, sfms_run_id))
        return await action()

    mocker.patch(f"{PIPELINE_PATH}._run_tracked_job", side_effect=run_tracked_job)
    fuel_type_raster, addresser, s3_client, session = (
        MagicMock(),
        MagicMock(),
        MagicMock(),
        MagicMock(),
    )
    run = a_run(date(2026, 6, 1), addresser=addresser, s3_client=s3_client, session=session)

    result = await run_temporal_fuel(run, fuel_type_raster)

    assert result == temporal_fuel
    assert tracked_jobs == [(SFMSRunLogJobName.TEMPORAL_FUEL, 42)]
    resolve.assert_awaited_once_with(date(2026, 6, 1), fuel_type_raster, addresser, s3_client)
    # the fuel grid is an FBP input and an output, and its Julian rasters are traced by archive key
    manifest = run.manifest
    assert manifest.input.fuel_raster.temporal == (
        "sfms_ng/fuel/temporal/2026/06/01/1/fbp2026_06_01_1.tif"
    )
    assert manifest.output.fuel_raster == "sfms_ng/fuel/temporal/2026/06/01/1/fbp2026_06_01_1.tif"
    assert manifest.input.julian_rasters == julian_archive_keys


@pytest.mark.anyio
async def test_run_weather_interpolation_records_statics_and_outputs(mocker: MockerFixture):
    addresser = MagicMock()
    addresser.get_mask_key.return_value = "/vsis3/some bucket/sfms/static/bc_mask.tif"
    addresser.get_dem_key.return_value = "/vsis3/some bucket/sfms/static/bc_elevation.tif"
    addresser.get_weather_key.side_effect = lambda datetime_utc, weather_param, run_type: (
        f"sfms_ng/{run_type.value}/{datetime_utc:%Y/%m/%d}/"
        f"{weather_param.value}_{datetime_utc:%Y%m%d}.tif"
    )
    mocker.patch.object(RasterProcessor, "process", new=AsyncMock(return_value="ignored.tif"))
    mocker.patch(f"{PIPELINE_PATH}._run_tracked_job", side_effect=_run_action)
    run = a_run(addresser=addresser)

    await run_weather_interpolation(
        run,
        "/vsis3/some bucket/fuel.tif",
        create_mock_sfms_actuals(),
    )

    assert run.manifest.input.static_rasters == {
        "dem": "sfms/static/bc_elevation.tif",
        "mask": "sfms/static/bc_mask.tif",
    }
    assert run.manifest.output.weather == {
        "temperature": "sfms_ng/actual/2025/07/04/temperature_20250704.tif",
        "relative_humidity": "sfms_ng/actual/2025/07/04/relative_humidity_20250704.tif",
        "wind_speed": "sfms_ng/actual/2025/07/04/wind_speed_20250704.tif",
        "wind_direction": "sfms_ng/actual/2025/07/04/wind_direction_20250704.tif",
        "precipitation": "sfms_ng/actual/2025/07/04/precipitation_20250704.tif",
    }


def stub_fwi_addresser(addresser: MagicMock) -> None:
    """Give an addresser realistic index and FWI input keys for the given run."""

    def index_key(datetime_utc, fwi_param, run_type):
        return (
            f"sfms_ng/{run_type.value}/{datetime_utc:%Y/%m/%d}/"
            f"{fwi_param.value}_{datetime_utc:%Y%m%d}.tif"
        )

    def fwi_inputs(datetime_to_process, fwi_param, run_type, previous_base_run_type=None):
        return FWIInputs(
            weather_keys={},
            index_keys={},
            output_key=index_key(datetime_to_process, fwi_param, run_type),
            run_type=run_type,
        )

    addresser.get_index_key.side_effect = index_key
    addresser.get_fwi_inputs.side_effect = fwi_inputs


@pytest.mark.anyio
async def test_run_fwi_calculations_records_seed_rasters_and_outputs(mocker: MockerFixture):
    addresser = MagicMock()
    stub_fwi_addresser(addresser)
    s3_client = MagicMock()
    s3_client.all_objects_exist = AsyncMock(return_value=True)
    mocker.patch(f"{PIPELINE_PATH}._run_tracked_job", side_effect=_run_action)
    fwi_processor = MagicMock()
    fwi_processor.calculate_index = AsyncMock()
    mocker.patch(f"{PIPELINE_PATH}.FWIProcessor", return_value=fwi_processor)
    run = a_run(addresser=addresser, s3_client=s3_client)

    calculated = await run_fwi_calculations(run)

    manifest = run.manifest
    assert calculated is True
    assert manifest.input.seed_rasters == {
        "ffmc": "sfms_ng/actual/2025/07/03/ffmc_20250703.tif",
        "dmc": "sfms_ng/actual/2025/07/03/dmc_20250703.tif",
        "dc": "sfms_ng/actual/2025/07/03/dc_20250703.tif",
    }
    assert manifest.output.fwi == {
        "ffmc": "sfms_ng/actual/2025/07/04/ffmc_20250704.tif",
        "dmc": "sfms_ng/actual/2025/07/04/dmc_20250704.tif",
        "dc": "sfms_ng/actual/2025/07/04/dc_20250704.tif",
        "isi": "sfms_ng/actual/2025/07/04/isi_20250704.tif",
        "bui": "sfms_ng/actual/2025/07/04/bui_20250704.tif",
        "fwi": "sfms_ng/actual/2025/07/04/fwi_20250704.tif",
    }


@pytest.mark.anyio
async def test_run_fwi_calculations_records_seeds_of_the_previous_base_run_type(
    mocker: MockerFixture,
):
    addresser = MagicMock()
    stub_fwi_addresser(addresser)
    s3_client = MagicMock()
    s3_client.all_objects_exist = AsyncMock(return_value=True)
    mocker.patch(f"{PIPELINE_PATH}._run_tracked_job", side_effect=_run_action)
    fwi_processor = MagicMock()
    fwi_processor.calculate_index = AsyncMock()
    mocker.patch(f"{PIPELINE_PATH}.FWIProcessor", return_value=fwi_processor)
    run = a_run(run_type=RunType.FORECAST, addresser=addresser, s3_client=s3_client)

    await run_fwi_calculations(run, previous_base_run_type=RunType.ACTUAL)

    # the first forecast day seeds from the previous actual run's rasters
    assert run.manifest.input.seed_rasters == {
        "ffmc": "sfms_ng/actual/2025/07/03/ffmc_20250703.tif",
        "dmc": "sfms_ng/actual/2025/07/03/dmc_20250703.tif",
        "dc": "sfms_ng/actual/2025/07/03/dc_20250703.tif",
    }


@pytest.mark.anyio
async def test_run_fwi_calculations_records_nothing_when_seeds_are_missing(
    mocker: MockerFixture,
):
    addresser = MagicMock()
    stub_fwi_addresser(addresser)
    s3_client = MagicMock()
    s3_client.all_objects_exist = AsyncMock(return_value=False)
    fwi_processor = MagicMock()
    fwi_processor.calculate_index = AsyncMock()
    mocker.patch(f"{PIPELINE_PATH}.FWIProcessor", return_value=fwi_processor)
    run = a_run(addresser=addresser, s3_client=s3_client)

    calculated = await run_fwi_calculations(run)

    assert calculated is False
    fwi_processor.calculate_index.assert_not_awaited()
    assert run.manifest.input.seed_rasters == {}
    assert run.manifest.output.fwi == {}
