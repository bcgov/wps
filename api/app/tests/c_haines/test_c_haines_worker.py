""" Very basic test for worker - essential just testing if it runs without exceptions """
import os
import pytest
import requests
from minio.datatypes import Object
from app import configure_logging
import app.c_haines.worker
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
    def mock_get_client(*args, **kwargs):
        """ mock get client """
        # class MockMinio(DefaultMockMinio):
        #     """ Mock minio object """

        #     def list_objects(self, bucket_name, prefix=None, recursive=False,
        #                      start_after=None, include_user_meta=False,
        #                      include_version=False, use_api_v1=False) -> Iterator[Object]:
        #         """ mock list objects.
        #         We want it to not find two files for the test, but find all others.
        #         """
        #         if prefix in ('c-haines-polygons/kml/GDPS/2020/5/21/0/2020-05-21T00:00:00.kml',
        #                       'c-haines-polygons/json/GDPS/2021/5/21/0/2021-05-21T00:00:00.json'):
        #             # The worker checks if the objects already exist.
        #             # We want two of those checks to come back with nothing (.e.g. no match found),
        #             # so that it will try to generate them.
        #             return iter([])
        #         else:
        #             # We want all other checks do come back with a match, so it doesn't generate them.
        #             return iter([prefix])

        # return MockMinio('blah'), 'blah'
        raise NotImplementedError()

    monkeypatch.setattr(app.c_haines.worker, 'get_client', mock_get_client)


@pytest.mark.usefixtures('mock_download', 'mock_s3_client')
def test_c_haines_worker():
    """ Test the c-haines worked.
    This is not a very focused test. Through the magic of sqlalchmy, it will only
    process one set of grib files. We check that the main process runs ok without raising
    any exceptions.
    """
    try:
        app.c_haines.worker.main()
    except Exception as exception:  # pylint: disable=broad-except
        pytest.fail(exception)
