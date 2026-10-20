"""Tests for the SFMS foliar moisture content step."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest_mock import MockerFixture
from wps_shared.db.models.sfms_run import SFMSRunLogJobName

from wps_sfms.fmc_step import calculate_fmc
from wps_sfms.processors.foliar_moisture_content import FoliarMoistureContentKeys
from wps_sfms.tests.run_test_utils import (
    a_run,
)

# manifest keys strip this bucket's GDAL prefix
pytestmark = pytest.mark.usefixtures("some_bucket")


@pytest.mark.anyio
async def test_fmc_step_records_its_failure(mocker: MockerFixture, tracked_jobs):
    processor = mocker.patch("wps_sfms.fmc_step.FoliarMoistureContentProcessor").return_value
    processor.process = AsyncMock(side_effect=RuntimeError("fmc failed"))
    addresser = MagicMock()
    addresser.get_fmc_inputs.return_value = MagicMock(
        elevation_key="sfms_ng/static/bc_elevation.tif",
        latitude_key="sfms_ng/static/latitude.tif",
        longitude_key="sfms_ng/static/longitude.tif",
    )
    run = a_run(addresser=addresser)

    with pytest.raises(RuntimeError, match="fmc failed"):
        await calculate_fmc(run)

    assert run.manifest.failed_step == SFMSRunLogJobName.FOLIAR_MOISTURE_CONTENT.value
    # its inputs were recorded before the calculation, its output only on success
    assert run.manifest.input.static_rasters == {
        "elevation": "sfms_ng/static/bc_elevation.tif",
        "latitude": "sfms_ng/static/latitude.tif",
        "longitude": "sfms_ng/static/longitude.tif",
    }
    assert run.manifest.input.fmc_raster is None
    assert run.manifest.output.fmc_raster is None
    assert run.manifest.reused.fmc_raster is None


def fmc_addresser() -> MagicMock:
    """An addresser whose FMC inputs write the target date's raster to a fixed key."""
    addresser = MagicMock()
    addresser.get_fmc_inputs.return_value = MagicMock(
        elevation_key="sfms_ng/static/bc_elevation.tif",
        latitude_key="sfms_ng/static/latitude.tif",
        longitude_key="sfms_ng/static/longitude.tif",
        output_keys={date(2025, 7, 4): "sfms_ng/fmc/fmc_20250704.tif"},
    )
    return addresser


@pytest.mark.anyio
async def test_fmc_step_records_a_calculated_raster_as_its_output(
    mocker: MockerFixture, tracked_jobs
):
    processor = mocker.patch("wps_sfms.fmc_step.FoliarMoistureContentProcessor").return_value
    processor.process = AsyncMock(
        return_value=FoliarMoistureContentKeys(
            processed_keys={date(2025, 7, 4): "sfms_ng/fmc/fmc_20250704.tif"}, reused_keys={}
        )
    )
    run = a_run(addresser=fmc_addresser())

    fmc_key = await calculate_fmc(run)

    assert fmc_key == "sfms_ng/fmc/fmc_20250704.tif"
    assert run.manifest.input.fmc_raster == "sfms_ng/fmc/fmc_20250704.tif"
    assert run.manifest.output.fmc_raster == "sfms_ng/fmc/fmc_20250704.tif"
    assert run.manifest.reused.fmc_raster is None


@pytest.mark.anyio
async def test_fmc_step_records_an_existing_raster_as_reused(mocker: MockerFixture, tracked_jobs):
    processor = mocker.patch("wps_sfms.fmc_step.FoliarMoistureContentProcessor").return_value
    # the raster already existed, so nothing was calculated
    processor.process = AsyncMock(
        return_value=FoliarMoistureContentKeys(
            processed_keys={}, reused_keys={date(2025, 7, 4): "sfms_ng/fmc/fmc_20250704.tif"}
        )
    )
    run = a_run(addresser=fmc_addresser())

    fmc_key = await calculate_fmc(run)

    assert fmc_key == "sfms_ng/fmc/fmc_20250704.tif"
    assert run.manifest.input.fmc_raster == "sfms_ng/fmc/fmc_20250704.tif"
    assert run.manifest.reused.fmc_raster == "sfms_ng/fmc/fmc_20250704.tif"
    assert run.manifest.output.fmc_raster is None
