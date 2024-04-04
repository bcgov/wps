""" Unit testing for ECMWF data processing """

import os
import pytest
from datetime import datetime, timezone, timedelta
from app.jobs.ecmwf import parse_url_for_timestamps
from app.jobs import ecmwf

@pytest.mark.parametrize(
    "date, cycle, step, expected_result",
    [
        ("20240331", "00z", "0h", (datetime(2024, 3, 31, 0, 0, 0).replace(tzinfo=timezone.utc),
                                    datetime(2024, 3, 31, 0, 0, 0).replace(tzinfo=timezone.utc))),
        ("20240331", "00z", "102h", (datetime(2024, 3, 31, 0, 0, 0).replace(tzinfo=timezone.utc),
                                     datetime(2024, 3, 31, 0, 0, 0).replace(tzinfo=timezone.utc) + timedelta(hours=102))),
        ("20240331", "12z", "0h", (datetime(2024, 3, 31, 12, 0, 0).replace(tzinfo=timezone.utc),
                                     datetime(2024, 3, 31, 12, 0, 0).replace(tzinfo=timezone.utc))),
        ("20240331", "12z", "132h", (datetime(2024, 3, 31, 12, 0, 0).replace(tzinfo=timezone.utc),
                                     datetime(2024, 3, 31, 12, 0, 0).replace(tzinfo=timezone.utc) + timedelta(hours=132))),
    ],
)
def test_parse_url_for_timestamps(date, cycle, step, expected_result):
   (model_timestamp, prediction_timestamp) = parse_url_for_timestamps(f"https://data.ecmwf.int/forecasts/{date}/{cycle}/ifs/0p25/oper/20240331000000-{step}-oper-fc.grib2")
   assert model_timestamp == expected_result[0]
   assert prediction_timestamp == expected_result[1]


def test_job():
    with pytest.raises(SystemExit) as excinfo:
        ecmwf.main()
    # Assert that we exited with an error code.
    assert excinfo.value.code == os.EX_OK