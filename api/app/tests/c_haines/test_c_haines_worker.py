""" Very basic test for worker - essential just testing if it runs without exceptions """
import os
import asyncio
import pytest
import requests
from aiobotocore.client import AioBaseClient
from app import configure_logging
import app.c_haines.worker
import app.c_haines.kml
from app.tests.common import MockResponse

configure_logging()


@pytest.fixture()
def mock_download(monkeypatch):
    """ fixture for env_canada.download """
    # pylint: disable=unused-argument
    def mock_requests_get(*args, **kwargs):
        """ mock env_canada download method """
        dirname = os.path.dirname(os.path.realpath(__file__))
        if 'TMP_ISBL' in args[0]:
            if '700' in args[0]:
                grib_filename = 'CMC_hrdps_continental_TMP_ISBL_0850_ps2.5km_2021012618_P048-00.grib2'
            if '850' in args[0]:
                grib_filename = 'CMC_hrdps_continental_TMP_ISBL_0700_ps2.5km_2021012618_P048-00.grib2'
        elif 'DEPR_ISBL' in args[0]:
            grib_filename = 'CMC_hrdps_continental_DEPR_ISBL_0850_ps2.5km_2021012618_P048-00.grib2'
        filename = os.path.join(dirname, grib_filename)
        with open(filename, 'rb') as file:
            content = file.read()
        return MockResponse(status_code=200, content=content)
    monkeypatch.setattr(requests, 'get', mock_requests_get)


@pytest.fixture()
def mock_s3_client(monkeypatch):
    """ mock s3 client """
    async def mock_object_exists_v2(target_path: str):
        """ mock object exists """
        return not (target_path in ('c-haines-polygons/kml/GDPS/2020/5/21/0/2020-05-21T00:00:00.kml',
                                    'c-haines-polygons/json/GDPS/2021/5/21/0/2021-05-21T00:00:00.json'))

    async def mock_object_exists(client: AioBaseClient, bucket: str, target_path: str):
        """ mock object exists """
        return not (target_path in ('c-haines-polygons/kml/GDPS/2020/5/21/0/2020-05-21T00:00:00.kml',
                                    'c-haines-polygons/json/GDPS/2021/5/21/0/2021-05-21T00:00:00.json'))

    monkeypatch.setattr(app.c_haines.severity_index, 'object_exists_v2', mock_object_exists_v2)
    monkeypatch.setattr(app.c_haines.severity_index, 'object_exists', mock_object_exists_v2)
    monkeypatch.setattr(app.c_haines.kml, 'object_exists', mock_object_exists)


@pytest.mark.usefixtures('mock_download', 'mock_s3_client')
def test_c_haines_worker():
    """ Test the c-haines worked.
    This is not a very focused test. Through the magic of sqlalchmy, it will only
    process one set of grib files. We check that the main process runs ok without raising
    any exceptions.
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(app.c_haines.worker.main())
    except Exception as exception:  # pylint: disable=broad-except
        pytest.fail(exception)
