"""Tests for the station danger rating step."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest_mock import MockerFixture
from wps_shared.db.models.sfms_run import SFMSRunLogJobName
from wps_shared.geospatial.geospatial import GDALResamplingMethod
from wps_shared.run_type import RunType

from wps_sfms.danger_rating_step import interpolate_danger_rating
from wps_sfms.tests.run_test_utils import a_run, station_weather

pytestmark = pytest.mark.usefixtures("some_bucket")


@pytest.mark.anyio
async def test_interpolates_and_records_danger_rating(mocker: MockerFixture, tracked_jobs):
    addresser = MagicMock()
    addresser.get_mask_key.return_value = "/vsis3/some bucket/sfms/static/bc_mask.tif"
    addresser.get_danger_rating_key.return_value = (
        "sfms_ng/forecast/2025/07/04/danger_rating_20250704.tif"
    )
    processor = MagicMock()
    processor.process = AsyncMock()
    constructor = mocker.patch(
        "wps_sfms.danger_rating_step.DangerRatingInterpolator", return_value=processor
    )
    run = a_run(for_date=date(2025, 7, 4), run_type=RunType.FORECAST, addresser=addresser)
    stations = station_weather()
    stations[0].danger_rating = 4

    output_key = await interpolate_danger_rating(run, stations)

    assert output_key == "sfms_ng/forecast/2025/07/04/danger_rating_20250704.tif"
    field = constructor.call_args.args[1]
    assert field.values.tolist() == [4.0, 0.0]
    processor.process.assert_awaited_once_with(
        run.s3_client,
        run.base_fuel_raster_path,
        output_key,
        cog_resample_alg=GDALResamplingMethod.NEAREST_NEIGHBOUR,
    )
    assert tracked_jobs == [SFMSRunLogJobName.DANGER_RATING_INTERPOLATION]
    assert run.manifest.input.static_rasters["mask"] == "sfms/static/bc_mask.tif"
    assert run.manifest.output.danger_rating_raster == output_key


@pytest.mark.anyio
async def test_failure_does_not_record_output(mocker: MockerFixture, tracked_jobs):
    processor = MagicMock()
    processor.process = AsyncMock(side_effect=RuntimeError("interpolation failed"))
    mocker.patch("wps_sfms.danger_rating_step.DangerRatingInterpolator", return_value=processor)
    run = a_run()

    with pytest.raises(RuntimeError, match="interpolation failed"):
        await interpolate_danger_rating(run, station_weather())

    assert run.manifest.output.danger_rating_raster is None
    assert run.manifest.failed_step == "danger_rating_interpolation"
    assert tracked_jobs == [SFMSRunLogJobName.DANGER_RATING_INTERPOLATION]
