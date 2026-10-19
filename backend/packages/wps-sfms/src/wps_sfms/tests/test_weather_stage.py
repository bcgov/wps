"""Tests for the SFMS weather interpolation stage."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest_mock import MockerFixture

from wps_sfms.processors.idw import RasterProcessor
from wps_sfms.tests.run_test_utils import (
    a_run,
    station_weather,
)
from wps_sfms.weather_stage import interpolate_weather

# manifest keys strip this bucket's GDAL prefix
pytestmark = pytest.mark.usefixtures("some_bucket")


@pytest.mark.anyio
async def test_weather_interpolation_stage_records_statics_and_outputs(
    mocker: MockerFixture, tracked_jobs
):
    addresser = MagicMock()
    addresser.get_mask_key.return_value = "/vsis3/some bucket/sfms/static/bc_mask.tif"
    addresser.get_dem_key.return_value = "/vsis3/some bucket/sfms/static/bc_elevation.tif"
    addresser.get_weather_key.side_effect = lambda datetime_utc, weather_param, run_type: (
        f"sfms_ng/{run_type.value}/{datetime_utc:%Y/%m/%d}/"
        f"{weather_param.value}_{datetime_utc:%Y%m%d}.tif"
    )
    mocker.patch.object(RasterProcessor, "process", new=AsyncMock(return_value="ignored.tif"))
    run = a_run(addresser=addresser)

    await interpolate_weather(run, station_weather())

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
