import os
from datetime import datetime, timezone

import pytest
from pytest_mock import MockerFixture

from app.jobs import sfms_calculations
from app.jobs.sfms_calculations import SFMSCalcJob


@pytest.mark.parametrize(
    "raster_function",
    [("calculate_bui"), ("calculate_daily_ffmc")],
)
def test_sfms_calc_job_fail_default(raster_function, monkeypatch, mocker: MockerFixture):
    async def mock_job_error():
        raise OSError("Error")

    monkeypatch.setattr(SFMSCalcJob, raster_function, mock_job_error)

    monkeypatch.setattr("sys.argv", ["sfms_calculations.py"])

    rocket_chat_spy = mocker.spy(sfms_calculations, "send_rocketchat_notification")

    with pytest.raises(SystemExit) as excinfo:
        sfms_calculations.main()
    # Assert that we exited with an error code
    assert excinfo.value.code == os.EX_SOFTWARE

    assert rocket_chat_spy.call_count == 1


def test_sfms_calc_job_cli_arg(monkeypatch, mocker: MockerFixture):
    bui_calc_spy = mocker.patch.object(SFMSCalcJob, "calculate_bui", return_value=None)
    daily_ffmc_calc_spy = mocker.patch.object(SFMSCalcJob, "calculate_daily_ffmc", return_value=None)

    test_datetime = "2024-10-10 5"
    monkeypatch.setattr("sys.argv", ["sfms_calculations.py", test_datetime])

    sfms_calculations.main()

    bui_calc_spy.assert_called_once_with(datetime.strptime(test_datetime, "%Y-%m-%d %H").replace(tzinfo=timezone.utc))
    daily_ffmc_calc_spy.assert_called_once_with(datetime.strptime(test_datetime, "%Y-%m-%d %H").replace(tzinfo=timezone.utc))


@pytest.mark.anyio
async def test_sfms_calc_job_cli_arg_missing_hour(monkeypatch):
    test_datetime = "2024-10-10"
    monkeypatch.setattr("sys.argv", ["sfms_calculations.py", test_datetime])

    with pytest.raises(SystemExit) as excinfo:
        await sfms_calculations.main()

    assert excinfo.value.code == 1
