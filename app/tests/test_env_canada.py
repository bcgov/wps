""" Unit tests for app/env_canada.py """

import os
import pytest
import wget
import env_canada
# pylint: disable=unused-argument, redefined-outer-name


FILENAME = 'CMC_glb_TMP_TGL_2_latlon.24x.24_2020071000_P000.grib2'
URL = 'https://this.is.env.weather.server'
PATH = os.path.dirname(os.path.realpath(__file__)) + '/downloads/gdps'


@pytest.fixture()
def mock_wget_download(monkeypatch):
    """ fixture for wget.download """
    def mock_download(*args):
        """ mock wget's download method """
        given_path = args[1]
        return given_path + FILENAME
    monkeypatch.setattr(wget, 'download', mock_download)


def test_get_download_urls():
    """ test to see if get_download_urls methods give the correct number of urls """
    total_num_of_urls = len(['00', '12']) * 81 * len(['TMP_TGL_2', 'RH_TGL_2'])
    assert len(env_canada.get_download_urls()) == total_num_of_urls


def test_failed_download():
    """ test to see if download behave correctly when failing to download """
    assert env_canada.download(URL, PATH) is None


def test_download(mock_wget_download):
    """ test to see if download behave correctly when downloading is successful """
    assert env_canada.download(URL, PATH) == PATH + FILENAME


def test_main(mock_wget_download):
    """ run main method to see if it runs successfully """
    env_canada.main()
