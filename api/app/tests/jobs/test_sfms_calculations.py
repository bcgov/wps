import os
from unittest.mock import AsyncMock
from pytest_mock import MockerFixture
import pytest

from app.utils.s3_client import S3Client
from app.sfms.date_range_processor import BUIDateRangeProcessor
from app.sfms.raster_addresser import FWIParameter, RasterKeyAddresser
from app.geospatial.wps_dataset import WPSDataset, multi_wps_dataset_context
from app.jobs.sfms_calculations import SFMSCalcJob
from app.jobs import sfms_calculations


def test_sfms_calc_job_fail(monkeypatch, mocker: MockerFixture):
    async def mock_job_error():
        raise OSError("Error")

    monkeypatch.setattr(SFMSCalcJob, "calculate_bui", mock_job_error)

    rocket_chat_spy = mocker.spy(sfms_calculations, "send_rocketchat_notification")

    with pytest.raises(SystemExit) as excinfo:
        sfms_calculations.main()
    # Assert that we exited with an error code.
    assert excinfo.value.code == os.EX_SOFTWARE
    # Assert that rocket chat was called.
    assert rocket_chat_spy.call_count == 1
