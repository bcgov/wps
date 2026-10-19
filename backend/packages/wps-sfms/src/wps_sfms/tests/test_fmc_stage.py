"""Tests for the SFMS foliar moisture content stage."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest_mock import MockerFixture
from wps_shared.db.models.sfms_run import SFMSRunLogJobName

from wps_sfms.fmc_stage import calculate_fmc
from wps_sfms.tests.run_test_utils import (
    a_run,
)

# manifest keys strip this bucket's GDAL prefix
pytestmark = pytest.mark.usefixtures("some_bucket")


@pytest.mark.anyio
async def test_fmc_stage_records_its_failure(mocker: MockerFixture, tracked_jobs):
    processor = mocker.patch("wps_sfms.fmc_stage.FoliarMoistureContentProcessor").return_value
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

    assert run.manifest.failed_stage == SFMSRunLogJobName.FOLIAR_MOISTURE_CONTENT.value
    # its inputs were recorded before the calculation, its output only on success
    assert run.manifest.input.static_rasters == {
        "elevation": "sfms_ng/static/bc_elevation.tif",
        "latitude": "sfms_ng/static/latitude.tif",
        "longitude": "sfms_ng/static/longitude.tif",
    }
    assert run.manifest.output.fmc_raster is None
