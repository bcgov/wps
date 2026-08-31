from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest_mock import MockerFixture
from wps_shared.db.models.sfms_run import SFMSRunLogJobName
from wps_shared.run_type import RunType

from app.jobs.sfms_run_pipeline import (
    _resolve_percent_conifer_path,
    _resolve_percent_dead_conifer_path,
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
async def test_run_fbp_calculations_resolves_inputs_and_tracks_sfc(mocker: MockerFixture):
    datetime_to_process = datetime(2025, 7, 4, 20, tzinfo=timezone.utc)
    addresser = MagicMock()
    s3_client = MagicMock()
    session = MagicMock()
    sfc_inputs = MagicMock()
    addresser.get_surface_fuel_consumption_inputs.return_value = sfc_inputs
    resolve_percent_conifer = mocker.patch(
        f"{PIPELINE_PATH}._resolve_percent_conifer_path",
        new=AsyncMock(return_value="/vsis3/test/sfms/static/m12_2025.tif"),
    )
    processor = MagicMock()
    processor.process = AsyncMock()
    processor_class = mocker.patch(
        f"{PIPELINE_PATH}.SurfaceFuelConsumptionProcessor", return_value=processor
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
    addresser.get_surface_fuel_consumption_inputs.assert_called_once_with(
        datetime_to_process,
        RunType.ACTUAL,
        "/vsis3/test/fuel.tif",
        "/vsis3/test/sfms/static/m12_2025.tif",
    )
    processor_class.assert_called_once_with(datetime_to_process)
    processor.process.assert_awaited_once()
    assert processor.process.await_args.args[0] is s3_client
    assert processor.process.await_args.args[2] is sfc_inputs
    assert tracked_jobs == [
        SFMSRunLogJobName.SFC_CALCULATION,
        SFMSRunLogJobName.ROS_CALCULATION,
    ]
