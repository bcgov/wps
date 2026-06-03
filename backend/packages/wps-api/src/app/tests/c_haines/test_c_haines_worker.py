"""Very basic test for worker - essential just testing if it runs without exceptions"""

import asyncio
import os

import pytest
import requests
from aiobotocore.client import AioBaseClient
from wps_shared.tests.common import MockResponse
from wps_shared.wps_logging import configure_logging

import app.c_haines.kml
import app.c_haines.worker

configure_logging()

TMP_700_FIXTURE = "20210126T18Z_MSC_HRDPS_TMP_ISBL_0700_RLatLon0.0225_PT048.grib2"
TMP_850_FIXTURE = "20210126T18Z_MSC_HRDPS_TMP_ISBL_0850_RLatLon0.0225_PT048.grib2"
DEW_850_FIXTURE = "20210126T18Z_MSC_HRDPS_DEPR_ISBL_0850_RLatLon0.0225_PT048.grib2"


@pytest.fixture()
def mock_download(monkeypatch):
    """fixture for env_canada.download"""

    def mock_requests_get(*args, **kwargs):
        """mock env_canada download method"""
        url = args[0]
        dirname = os.path.dirname(os.path.realpath(__file__))
        fixture_by_level = {
            "AirTemp_IsbL-0700": TMP_700_FIXTURE,
            "TMP_ISBL_0700": TMP_700_FIXTURE,
            "AirTemp_IsbL-0850": TMP_850_FIXTURE,
            "TMP_ISBL_0850": TMP_850_FIXTURE,
            "DewPointDepression_IsbL-0850": DEW_850_FIXTURE,
            "DEPR_ISBL_0850": DEW_850_FIXTURE,
        }
        grib_filename = next(
            (filename for level, filename in fixture_by_level.items() if level in url),
            None,
        )
        if grib_filename is None:
            raise AssertionError(f"No c-haines GRIB fixture mapped for {url}")
        filename = os.path.join(dirname, grib_filename)
        with open(filename, "rb") as file:
            content = file.read()
        return MockResponse(status_code=200, content=content)

    monkeypatch.setattr(requests, "get", mock_requests_get)


@pytest.fixture()
def mock_s3_client(monkeypatch):
    """mock s3 client"""

    async def mock_object_exists_v2(target_path: str):
        """mock object exists"""
        return target_path not in (
            "c-haines-polygons/kml/GDPS/2020/5/21/0/2020-05-21T00:00:00.kml",
            "c-haines-polygons/json/GDPS/2021/5/21/0/2021-05-21T00:00:00.json",
        )

    async def mock_object_exists(client: AioBaseClient, bucket: str, target_path: str):
        """mock object exists"""
        return target_path not in (
            "c-haines-polygons/kml/GDPS/2020/5/21/0/2020-05-21T00:00:00.kml",
            "c-haines-polygons/json/GDPS/2021/5/21/0/2021-05-21T00:00:00.json",
        )

    monkeypatch.setattr(app.c_haines.severity_index, "object_exists_v2", mock_object_exists_v2)
    monkeypatch.setattr(app.c_haines.severity_index, "object_exists", mock_object_exists)
    monkeypatch.setattr(app.c_haines.kml, "object_exists", mock_object_exists)


@pytest.mark.usefixtures("mock_download", "mock_s3_client")
def test_c_haines_worker():
    """Test the c-haines worked.
    This is not a very focused test. Through the magic of sqlalchmy, it will only
    process one set of grib files. We check that the main process runs ok without raising
    any exceptions.
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(app.c_haines.worker.main())
    except Exception as exception:
        pytest.fail(str(exception))
