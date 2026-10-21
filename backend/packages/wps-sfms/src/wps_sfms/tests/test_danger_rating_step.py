"""Tests for the station danger rating step."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest_mock import MockerFixture
from wps_shared.db.models.sfms_run import SFMSRunLogJobName
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
    constructor = mocker.patch("wps_sfms.danger_rating_step.Interpolator", return_value=processor)
    run = a_run(for_date=date(2025, 7, 4), run_type=RunType.FORECAST, addresser=addresser)
    stations = station_weather()
    stations[0].danger_rating = 4

    output_key = await interpolate_danger_rating(run, stations)

    assert output_key == "sfms_ng/forecast/2025/07/04/danger_rating_20250704.tif"
    field = constructor.call_args.args[1]
    assert field.values.tolist() == [4.0]
    assert field.lats.tolist() == [49.0]
    processor.process.assert_awaited_once_with(
        run.s3_client,
        run.base_fuel_raster_path,
        output_key,
    )
    assert tracked_jobs == [SFMSRunLogJobName.DANGER_RATING_INTERPOLATION]
    assert run.manifest.output.danger_rating_raster == output_key


@pytest.mark.anyio
async def test_skips_when_no_stations_have_danger_rating(mocker: MockerFixture, tracked_jobs):
    constructor = mocker.patch("wps_sfms.danger_rating_step.Interpolator")
    chatops = mocker.patch("wps_sfms.danger_rating_step.send_chatops_notification")
    run = a_run()

    result = await interpolate_danger_rating(run, station_weather())

    assert result is None
    constructor.assert_not_called()
    run.raster_addresser.get_danger_rating_key.assert_not_called()
    assert tracked_jobs == []
    assert run.manifest.output.danger_rating_raster is None
    message, reason = chatops.call_args.args
    assert message == "Could not generate SFMS danger rating raster for actual 2025-07-04"
    assert str(reason) == "No stations have a danger rating"
    assert chatops.call_args.kwargs == {"severity": "warning"}


@pytest.mark.anyio
async def test_failure_does_not_record_output(mocker: MockerFixture, tracked_jobs):
    processor = MagicMock()
    processor.process = AsyncMock(side_effect=RuntimeError("interpolation failed"))
    mocker.patch("wps_sfms.danger_rating_step.Interpolator", return_value=processor)
    run = a_run()
    stations = station_weather()
    stations[0].danger_rating = 4

    with pytest.raises(RuntimeError, match="interpolation failed"):
        await interpolate_danger_rating(run, stations)

    assert run.manifest.output.danger_rating_raster is None
    assert run.manifest.failed_step == "danger_rating_interpolation"
    assert tracked_jobs == [SFMSRunLogJobName.DANGER_RATING_INTERPOLATION]
