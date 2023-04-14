""" Unit tests for app/jobs/noaa.py """

import os
import logging
from datetime import datetime, timezone
from app.jobs import common_model_fetchers
from app.tests.weather_models.test_models_common import MockResponse, shape, mock_get_model_run_predictions
import app.utils.time as time_utils
import pytest
import requests
from geoalchemy2.shape import from_shape
from app.db.models.weather_models import (PredictionModel,
                                          PredictionModelGridSubset, PredictionModelRunTimestamp,
                                          ProcessedModelRunUrl)
from app.jobs import noaa
import app.db.crud.weather_models


logger = logging.getLogger(__name__)


@pytest.fixture()
def mock_get_model_run_predictions_for_grid(monkeypatch):
    """ Mock out call to DB returning predictions """

    monkeypatch.setattr(
        common_model_fetchers, 'get_model_run_predictions_for_grid', mock_get_model_run_predictions)


@pytest.fixture()
def mock_database(monkeypatch):
    """ Mocked out database queries """
    gfs_url = ('https://www.ncei.noaa.gov/data/global-forecast-system/access/grid-004-0.5-degree/'
               'forecast/202302/20230219/gfs_4_20230219_0600_018.grb2')
    gfs_processed_model_run = ProcessedModelRunUrl(url=gfs_url)
    gfs_prediction_model = PredictionModel(id=1,
                                           abbreviation='GFS',
                                           projection='lonlat.0.5deg',
                                           name='Global Forecast System')
    gfs_prediction_model_run = PredictionModelRunTimestamp(
        id=1, prediction_model_id=1, prediction_run_timestamp=time_utils.get_utc_now(),
        prediction_model=gfs_prediction_model, complete=True)

    def mock_get_gfs_prediction_model_run_timestamp_records(*args, **kwargs):
        return [(gfs_prediction_model_run, gfs_prediction_model)]

    def mock_get_processed_file_record(session, url: str):
        # We only want the one file to be processed - otherwise our test takes forever
        if url != gfs_url:
            return gfs_processed_model_run
        return None

    def mock_get_grids_for_coordinate(session, prediction_model, coordinate):
        return [PredictionModelGridSubset(
            id=1, prediction_model_id=gfs_prediction_model.id, geom=from_shape(shape)), ]

    def mock_get_prediction_run(*args, **kwargs):
        return gfs_prediction_model_run

    monkeypatch.setattr(noaa, 'get_processed_file_record', mock_get_processed_file_record)
    monkeypatch.setattr(common_model_fetchers, 'get_prediction_model_run_timestamp_records',
                        mock_get_gfs_prediction_model_run_timestamp_records)
    monkeypatch.setattr(common_model_fetchers, 'get_grids_for_coordinate', mock_get_grids_for_coordinate)
    monkeypatch.setattr(app.db.crud.weather_models, 'get_prediction_run', mock_get_prediction_run)


@pytest.fixture()
def mock_download(monkeypatch):
    """ fixture for NOAA download """
    def mock_requests_get_gfs(*args, **kwargs):
        """ mock common_model_fetchers download method for GFS """
        dirname = os.path.dirname(os.path.realpath(__file__))
        filename = os.path.join(
            dirname, 'gfs_4_20230219_0600_018.grb2')
        with open(filename, 'rb') as file:
            content = file.read()
        return MockResponse(status_code=200, content=content)
    monkeypatch.setattr(requests, 'get', mock_requests_get_gfs)


def test_get_gfs_model_run_download_urls_for_00_utc():
    # March 2 at 00:00 UTC is equivalent to March 1 in Eastern timezone - should return URL for previous day
    # for a given date and model run cycle, there should be 2 time intervals * 10 days into future (11 days total)
    expected_num_of_urls = 2 * 11
    actual_urls = list(noaa.get_gfs_model_run_download_urls(datetime(2023, 3, 2, 00, tzinfo=timezone.utc), '00'))
    assert len(actual_urls) == expected_num_of_urls
    assert actual_urls[0] == noaa.GFS_BASE_URL + 'dir=%2Fgfs.20230301%2F00%2Fatmos&file=gfs.t00z.pgrb2.0p25.f018&var_APCP=on&var_RH=on&var_TMP=on&var_UGRD=on&var_VGRD=on&lev_surface=on&lev_2_m_above_ground=on&lev_10_m_above_ground=on&subregion=&toplat=60&leftlon=-139&rightlon=-114&bottomlat=48'
    assert actual_urls[-1] == noaa.GFS_BASE_URL + 'dir=%2Fgfs.20230301%2F00%2Fatmos&file=gfs.t00z.pgrb2.0p25.f261&var_APCP=on&var_RH=on&var_TMP=on&var_UGRD=on&var_VGRD=on&lev_surface=on&lev_2_m_above_ground=on&lev_10_m_above_ground=on&subregion=&toplat=60&leftlon=-139&rightlon=-114&bottomlat=48'


def test_get_gfs_model_run_download_urls_for_06_utc():
    # Feb 15 at 06:00 UTC is still Feb 15 (at 02:00) in Eastern timezone - should return URL for same day
    # for a given date and model run cycle, there should be 2 time intervals * 10 days into future (11 days total incl. today)
    expected_num_of_urls = 2 * 11
    actual_urls = list(noaa.get_gfs_model_run_download_urls(datetime(2023, 2, 15, 6, tzinfo=timezone.utc), '06'))
    assert len(actual_urls) == expected_num_of_urls
    assert actual_urls[0] == noaa.GFS_BASE_URL + 'dir=%2Fgfs.20230215%2F06%2Fatmos&file=gfs.t06z.pgrb2.0p25.f012&var_APCP=on&var_RH=on&var_TMP=on&var_UGRD=on&var_VGRD=on&lev_surface=on&lev_2_m_above_ground=on&lev_10_m_above_ground=on&subregion=&toplat=60&leftlon=-139&rightlon=-114&bottomlat=48'
    assert actual_urls[1] == noaa.GFS_BASE_URL + 'dir=%2Fgfs.20230215%2F06%2Fatmos&file=gfs.t06z.pgrb2.0p25.f015&var_APCP=on&var_RH=on&var_TMP=on&var_UGRD=on&var_VGRD=on&lev_surface=on&lev_2_m_above_ground=on&lev_10_m_above_ground=on&subregion=&toplat=60&leftlon=-139&rightlon=-114&bottomlat=48'
    assert actual_urls[-1] == noaa.GFS_BASE_URL + 'dir=%2Fgfs.20230215%2F06%2Fatmos&file=gfs.t06z.pgrb2.0p25.f255&var_APCP=on&var_RH=on&var_TMP=on&var_UGRD=on&var_VGRD=on&lev_surface=on&lev_2_m_above_ground=on&lev_10_m_above_ground=on&subregion=&toplat=60&leftlon=-139&rightlon=-114&bottomlat=48'


def test_get_gfs_model_run_download_urls_for_12_utc():
    # March 9 at 12:00 UTC is still March 9 in Eastern timezone - should return URL for same day
    # for a given date and model run cycle, there should be 2 time intervals * 10 days into future (11 days total incl. today)
    expected_num_of_urls = 2 * 11
    actual_urls = list(noaa.get_gfs_model_run_download_urls(datetime(2023, 3, 9, 12, tzinfo=timezone.utc), '12'))
    assert len(actual_urls) == expected_num_of_urls
    assert actual_urls[0] == noaa.GFS_BASE_URL + 'dir=%2Fgfs.20230309%2F12%2Fatmos&file=gfs.t12z.pgrb2.0p25.f006&var_APCP=on&var_RH=on&var_TMP=on&var_UGRD=on&var_VGRD=on&lev_surface=on&lev_2_m_above_ground=on&lev_10_m_above_ground=on&subregion=&toplat=60&leftlon=-139&rightlon=-114&bottomlat=48'
    assert actual_urls[1] == noaa.GFS_BASE_URL + 'dir=%2Fgfs.20230309%2F12%2Fatmos&file=gfs.t12z.pgrb2.0p25.f009&var_APCP=on&var_RH=on&var_TMP=on&var_UGRD=on&var_VGRD=on&lev_surface=on&lev_2_m_above_ground=on&lev_10_m_above_ground=on&subregion=&toplat=60&leftlon=-139&rightlon=-114&bottomlat=48'
    assert actual_urls[-1] == noaa.GFS_BASE_URL + 'dir=%2Fgfs.20230309%2F12%2Fatmos&file=gfs.t12z.pgrb2.0p25.f249&var_APCP=on&var_RH=on&var_TMP=on&var_UGRD=on&var_VGRD=on&lev_surface=on&lev_2_m_above_ground=on&lev_10_m_above_ground=on&subregion=&toplat=60&leftlon=-139&rightlon=-114&bottomlat=48'


def test_get_gfs_model_run_download_urls_for_18_utc():
    # Jan 27 at 18:00 UTC is still Jan 27 in Eastern timezone - should return URL for same day
    # for a given date and model run cycle, there should be 2 time intervals * 10 days into future (11 days total incl. today)
    expected_num_of_urls = 2 * 11
    actual_urls = list(noaa.get_gfs_model_run_download_urls(datetime(2023, 1, 27, 18, tzinfo=timezone.utc), '18'))
    assert len(actual_urls) == expected_num_of_urls
    assert actual_urls[0] == noaa.GFS_BASE_URL + 'dir=%2Fgfs.20230127%2F18%2Fatmos&file=gfs.t18z.pgrb2.0p25.f000&var_APCP=on&var_RH=on&var_TMP=on&var_UGRD=on&var_VGRD=on&lev_surface=on&lev_2_m_above_ground=on&lev_10_m_above_ground=on&subregion=&toplat=60&leftlon=-139&rightlon=-114&bottomlat=48'
    assert actual_urls[1] == noaa.GFS_BASE_URL + 'dir=%2Fgfs.20230127%2F18%2Fatmos&file=gfs.t18z.pgrb2.0p25.f003&var_APCP=on&var_RH=on&var_TMP=on&var_UGRD=on&var_VGRD=on&lev_surface=on&lev_2_m_above_ground=on&lev_10_m_above_ground=on&subregion=&toplat=60&leftlon=-139&rightlon=-114&bottomlat=48'
    assert actual_urls[-1] == noaa.GFS_BASE_URL + 'dir=%2Fgfs.20230127%2F18%2Fatmos&file=gfs.t18z.pgrb2.0p25.f243&var_APCP=on&var_RH=on&var_TMP=on&var_UGRD=on&var_VGRD=on&lev_surface=on&lev_2_m_above_ground=on&lev_10_m_above_ground=on&subregion=&toplat=60&leftlon=-139&rightlon=-114&bottomlat=48'


def test_parse_url_for_timestamps_simple():
    """ simple test case for noaa.parse_url_for_timestamps(): model_run_timestamp and prediction_timestamp
    are on the same day """
    url = 'https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl?dir=%2Fgfs.20230413%2F12%2Fatmos&file=gfs.t12z.pgrb2.0p25.f006&var_APCP=on&var_RH=on&var_TMP=on&var_UGRD=on&var_VGRD=on&lev_surface=on&lev_2_m_above_ground=on&lev_10_m_above_ground=on&subregion=&toplat=60&leftlon=-139&rightlon=-114&bottomlat=48'
    expected_model_run_timestamp = datetime(2023, 4, 13, 12, 0, tzinfo=timezone.utc)
    expected_prediction_timestamp = datetime(2023, 4, 13, 18, 0, tzinfo=timezone.utc)
    actual_model_run_timestamp, actual_prediction_timestamp = noaa.parse_url_for_timestamps(url)
    assert expected_model_run_timestamp == actual_model_run_timestamp
    assert expected_prediction_timestamp == actual_prediction_timestamp


def test_parse_url_for_timestamps_complex():
    """ more complex test case for noaa.parse_url_for_timestamps(): model_run_timestamp and
    prediction_timestamp are on different days """
    url = 'https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl?dir=%2Fgfs.20230413%2F18%2Fatmos&file=gfs.t18z.pgrb2.0p25.f243&var_APCP=on&var_RH=on&var_TMP=on&var_UGRD=on&var_VGRD=on&lev_surface=on&lev_2_m_above_ground=on&lev_10_m_above_ground=on&subregion=&toplat=60&leftlon=-139&rightlon=-114&bottomlat=48'
    expected_model_run_timestamp = datetime(2023, 4, 13, 18, 0, tzinfo=timezone.utc)
    expected_prediction_timestamp = datetime(2023, 4, 23, 21, 0, tzinfo=timezone.utc)
    actual_model_run_timestamp, actual_prediction_timestamp = noaa.parse_url_for_timestamps(url)
    assert expected_model_run_timestamp == actual_model_run_timestamp
    assert expected_prediction_timestamp == actual_prediction_timestamp


def test_get_year_mo_date_string_from_datetime():
    test_cases = [
        {
            'date': datetime(2023, 2, 14, 0, tzinfo=timezone.utc),
            'expected_year_mo_date': '20230214'
        },
        {
            'date': datetime(2023, 6, 5, 0, tzinfo=timezone.utc),
            'expected_year_mo_date': '20230605'
        },
        {
            'date': datetime(2023, 10, 31, 20, tzinfo=timezone.utc),
            'expected_year_mo_date': '20231031'
        },
    ]
    for test in test_cases:
        actual_string = noaa.get_year_mo_date_string_from_datetime(test.get('date'))
        assert test.get('expected_year_mo_date') == actual_string
