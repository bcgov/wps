from contextlib import asynccontextmanager
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest_mock import MockerFixture
from wps_shared.db.models.sfms_run import SFMSRunLogJobName
from wps_shared.db.models.temporal_fuel_raster import TemporalFuelRaster
from wps_shared.run_type import RunType

from app.jobs.sfms_run_pipeline import (
    _resolve_percent_conifer_path,
    _resolve_percent_dead_conifer_path,
    resolve_temporal_fuel_raster,
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
        "/vsis3/test/fuel.tif",
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


@pytest.fixture
def temporal_fuel_deps(mocker: MockerFixture):
    session = MagicMock()

    @asynccontextmanager
    async def _write_scope():
        yield session

    mocker.patch(f"{PIPELINE_PATH}.get_async_write_session_scope", _write_scope)
    s3_client = MagicMock()
    s3_client.get_content_hash = AsyncMock(side_effect=["on-hash", "off-hash"])
    publish = mocker.patch(
        f"{PIPELINE_PATH}.publish_temporal_fuel_raster",
        new_callable=AsyncMock,
        return_value="temporal-hash",
    )
    fuel_type_raster = MagicMock(id=7, object_store_path="sfms/static/fuel/2026/fbp2026_v1.tif")
    return session, s3_client, publish, fuel_type_raster


@pytest.mark.anyio
async def test_resolve_temporal_fuel_raster_reuses_matching_raster(
    mocker: MockerFixture, temporal_fuel_deps
):
    session, s3_client, publish, fuel_type_raster = temporal_fuel_deps
    existing = MagicMock(object_store_path="sfms_ng/fuel/temporal/existing.tif")
    get_existing = mocker.patch(
        f"{PIPELINE_PATH}.get_temporal_fuel_raster", new_callable=AsyncMock, return_value=existing
    )
    addresser = MagicMock()
    addresser.gdal_path.side_effect = lambda key: f"/vsis3/bucket/{key}"

    result = await resolve_temporal_fuel_raster(
        date(2026, 6, 1), fuel_type_raster, addresser, s3_client
    )

    assert result == "/vsis3/bucket/sfms_ng/fuel/temporal/existing.tif"
    assert get_existing.call_args.args[1:] == (date(2026, 6, 1), 7, "on-hash", "off-hash")
    publish.assert_not_awaited()
    session.add.assert_not_called()


@pytest.mark.anyio
async def test_resolve_temporal_fuel_raster_records_next_version(
    mocker: MockerFixture, temporal_fuel_deps
):
    session, s3_client, publish, fuel_type_raster = temporal_fuel_deps
    mocker.patch(
        f"{PIPELINE_PATH}.get_temporal_fuel_raster", new_callable=AsyncMock, return_value=None
    )
    mocker.patch(
        f"{PIPELINE_PATH}.get_latest_temporal_fuel_raster_version",
        new_callable=AsyncMock,
        return_value=2,
    )
    addresser = MagicMock()
    addresser.gdal_path.side_effect = lambda key: f"/vsis3/bucket/{key}"
    addresser.get_temporal_fuel_key.return_value = "temporal/3/fbp.tif"
    addresser.get_temporal_fuel_metadata_key.return_value = "temporal/3/fbp.json"

    result = await resolve_temporal_fuel_raster(
        date(2026, 6, 1), fuel_type_raster, addresser, s3_client
    )

    assert result == "/vsis3/bucket/temporal/3/fbp.tif"
    addresser.get_temporal_fuel_key.assert_called_once_with(date(2026, 6, 1), 3)
    publish.assert_awaited_once()
    record: TemporalFuelRaster = session.add.call_args.args[0]
    assert (record.fuel_type_raster_id, record.for_date, record.version) == (
        7,
        date(2026, 6, 1),
        3,
    )
    assert record.object_store_path == "temporal/3/fbp.tif"
    assert record.metadata_object_store_path == "temporal/3/fbp.json"
    assert record.content_hash == "temporal-hash"
    assert (record.green_up_on_hash, record.green_up_off_hash) == ("on-hash", "off-hash")
