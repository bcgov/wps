"""Tests for the SFMS primary fire behaviour prediction step."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest_mock import MockerFixture
from wps_shared.db.models.sfms_run import SFMSRunLogJobName
from wps_shared.run_type import RunType
from wps_shared.sfms.raster_addresser import (
    FBPParameter,
)

from wps_sfms.fbp_step import (
    _resolve_percent_conifer_path,
    calculate_primary_fbp,
)
from wps_sfms.tests.run_test_utils import (
    FMC_KEY,
    FWI_KEYS,
    WEATHER_KEYS,
    a_run,
)

# manifest keys strip this bucket's GDAL prefix
pytestmark = pytest.mark.usefixtures("some_bucket")


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
async def test_primary_fbp_step_runs_one_tracked_primary_calculation(
    mocker: MockerFixture,
    tracked_jobs,
):
    datetime_to_process = datetime(2025, 7, 4, 20, tzinfo=timezone.utc)
    addresser = MagicMock()
    addresser.get_slope_key.side_effect = lambda: "sfms_ng/static/bc_slope.tif"
    addresser.get_aspect_key.side_effect = lambda: "sfms_ng/static/bc_aspect.tif"
    addresser.gdal_path.side_effect = lambda key: f"/vsis3/some bucket/{key}"
    s3_client = MagicMock()
    fbp_output_keys = {
        parameter: f"sfms_ng/actual/2025/07/04/{parameter.value}_20250704.tif"
        for parameter in FBPParameter
    }
    primary_inputs = MagicMock()
    primary_inputs.output_keys = fbp_output_keys
    addresser.get_primary_fire_behaviour_inputs.return_value = primary_inputs
    resolve_percent_conifer = mocker.patch(
        "wps_sfms.fbp_step._resolve_percent_conifer_path",
        new=AsyncMock(return_value="/vsis3/some bucket/sfms/static/m12_2025.tif"),
    )
    primary_processor = MagicMock()
    primary_processor.process = AsyncMock()
    primary_processor_class = mocker.patch(
        "wps_sfms.fbp_step.PrimaryFireBehaviourProcessor", return_value=primary_processor
    )
    run = a_run(addresser=addresser, s3_client=s3_client)

    await calculate_primary_fbp(run, "/vsis3/some bucket/fuel.tif", FMC_KEY, WEATHER_KEYS, FWI_KEYS)

    resolve_percent_conifer.assert_awaited_once_with(2025, addresser, s3_client)
    addresser.get_primary_fire_behaviour_inputs.assert_called_once_with(
        datetime_to_process,
        RunType.ACTUAL,
        "/vsis3/some bucket/fuel.tif",
        "/vsis3/some bucket/sfms/static/m12_2025.tif",
        # FFMC, BUI, wind and FMC are the raster keys the step was handed
        "/vsis3/some bucket/sfms_ng/actual/2025/07/04/ffmc_20250704.tif",
        "/vsis3/some bucket/sfms_ng/actual/2025/07/04/bui_20250704.tif",
        "/vsis3/some bucket/sfms_ng/actual/2025/07/04/wind_speed_20250704.tif",
        "/vsis3/some bucket/sfms_ng/actual/2025/07/04/wind_direction_20250704.tif",
        "/vsis3/some bucket/sfms_ng/static/fmc/2025/07/04/fmc_20250704.tif",
        "/vsis3/some bucket/sfms_ng/static/bc_slope.tif",
        "/vsis3/some bucket/sfms_ng/static/bc_aspect.tif",
    )
    primary_processor_class.assert_called_once_with(datetime_to_process)
    primary_processor.process.assert_awaited_once()
    assert primary_processor.process.await_args.args[0] is s3_client
    assert primary_processor.process.await_args.args[2] is primary_inputs
    assert tracked_jobs == [SFMSRunLogJobName.PRIMARY_FBP_CALCULATION]

    # the manifest records the percent-conifer and terrain rasters FBP read, and its outputs
    assert run.manifest.input.fuel_raster.percent_conifer == "sfms/static/m12_2025.tif"
    assert run.manifest.input.static_rasters == {
        "slope": "sfms_ng/static/bc_slope.tif",
        "aspect": "sfms_ng/static/bc_aspect.tif",
    }
    assert run.manifest.output.fbp == {
        parameter.value: key for parameter, key in fbp_output_keys.items()
    }


@pytest.mark.anyio
async def test_primary_fbp_step_records_its_inputs_but_no_outputs_when_it_fails(
    mocker: MockerFixture, tracked_jobs
):
    addresser = MagicMock()
    addresser.get_slope_key.side_effect = lambda: "sfms_ng/static/bc_slope.tif"
    addresser.get_aspect_key.side_effect = lambda: "sfms_ng/static/bc_aspect.tif"
    addresser.gdal_path.side_effect = lambda key: f"/vsis3/some bucket/{key}"
    mocker.patch(
        "wps_sfms.fbp_step._resolve_percent_conifer_path",
        new=AsyncMock(return_value="/vsis3/some bucket/sfms/static/m12_2025.tif"),
    )
    processor = mocker.patch("wps_sfms.fbp_step.PrimaryFireBehaviourProcessor").return_value
    processor.process = AsyncMock(side_effect=RuntimeError("fbp failed"))
    run = a_run(addresser=addresser)

    with pytest.raises(RuntimeError, match="fbp failed"):
        await calculate_primary_fbp(
            run, "/vsis3/some bucket/fuel.tif", FMC_KEY, WEATHER_KEYS, FWI_KEYS
        )

    assert run.manifest.failed_step == SFMSRunLogJobName.PRIMARY_FBP_CALCULATION.value
    assert run.manifest.input.static_rasters == {
        "slope": "sfms_ng/static/bc_slope.tif",
        "aspect": "sfms_ng/static/bc_aspect.tif",
    }
    assert run.manifest.input.fuel_raster.percent_conifer == "sfms/static/m12_2025.tif"
    assert run.manifest.output.fbp == {}
