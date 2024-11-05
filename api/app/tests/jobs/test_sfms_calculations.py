import os
from datetime import datetime, timezone

import pytest
from pytest_mock import MockerFixture

from app.jobs import sfms_calculations
from app.jobs.sfms_calculations import SFMSCalcJob
from app.utils.time import get_utc_now


def test_sfms_calc_job_fail_default(monkeypatch, mocker: MockerFixture):
    async def mock_job_error():
        raise OSError("Error")

    monkeypatch.setattr(SFMSCalcJob, "calculate_bui", mock_job_error)

    monkeypatch.setattr("sys.argv", ["sfms_calculations.py"])

    rocket_chat_spy = mocker.spy(sfms_calculations, "send_rocketchat_notification")

    with pytest.raises(SystemExit) as excinfo:
        sfms_calculations.main()
    # Assert that we exited with an error code
    assert excinfo.value.code == os.EX_SOFTWARE

    assert rocket_chat_spy.call_count == 1


@pytest.mark.anyio
async def test_sfms_calc_job_cli_arg(monkeypatch, mocker: MockerFixture):
    monkeypatch.setattr(SFMSCalcJob, "calculate_bui", None)

    calc_spy = mocker.spy(SFMSCalcJob, "calculate_bui")

    test_datetime = get_utc_now().strftime("%Y-%m-%d %H")
    monkeypatch.setattr("sys.argv", ["sfms_calculations.py", test_datetime])

    with pytest.raises(SystemExit) as excinfo:
        await sfms_calculations.main()

    assert excinfo.value.code == os.EX_SOFTWARE

    called_args, _ = calc_spy.call_args
    assert called_args[0] == datetime.strptime(test_datetime, "%Y-%m-%d %H").replace(tzinfo=timezone.utc)
