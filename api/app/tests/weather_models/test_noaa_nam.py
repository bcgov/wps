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


# @pytest.fixture()
# def mock_get_model_run_predictions_for_grid(monkeypatch):
#     """ Mock out call to DB returning predictions """

#     monkeypatch.setattr(
#         common_model_fetchers, 'get_model_run_predictions_for_grid', mock_get_model_run_predictions)


# @pytest.fixture()
# def mock_database(monkeypatch):
#     """ Mocked out database queries """
#     gfs_url = ('https://www.ncei.noaa.gov/data/global-forecast-system/access/grid-004-0.5-degree/'
#                'forecast/202302/20230219/gfs_4_20230219_0600_018.grb2')
#     gfs_processed_model_run = ProcessedModelRunUrl(url=gfs_url)
#     gfs_prediction_model = PredictionModel(id=1,
#                                            abbreviation='GFS',
#                                            projection='lonlat.0.25deg',
#                                            name='Global Forecast System')
#     gfs_prediction_model_run = PredictionModelRunTimestamp(
#         id=1, prediction_model_id=1, prediction_run_timestamp=time_utils.get_utc_now(),
#         prediction_model=gfs_prediction_model, complete=True)

#     def mock_get_gfs_prediction_model_run_timestamp_records(*args, **kwargs):
#         return [(gfs_prediction_model_run, gfs_prediction_model)]

#     def mock_get_processed_file_record(session, url: str):
#         # We only want the one file to be processed - otherwise our test takes forever
#         if url != gfs_url:
#             return gfs_processed_model_run
#         return None

#     def mock_get_grids_for_coordinate(session, prediction_model, coordinate):
#         return [PredictionModelGridSubset(
#             id=1, prediction_model_id=gfs_prediction_model.id, geom=from_shape(shape)), ]

#     def mock_get_prediction_run(*args, **kwargs):
#         return gfs_prediction_model_run

#     monkeypatch.setattr(noaa, 'get_processed_file_record', mock_get_processed_file_record)
#     monkeypatch.setattr(common_model_fetchers, 'get_prediction_model_run_timestamp_records',
#                         mock_get_gfs_prediction_model_run_timestamp_records)
#     monkeypatch.setattr(common_model_fetchers, 'get_grids_for_coordinate', mock_get_grids_for_coordinate)
#     monkeypatch.setattr(app.db.crud.weather_models, 'get_prediction_run', mock_get_prediction_run)


# @pytest.fixture()
# def mock_download(monkeypatch):
#     """ fixture for NOAA download """
#     def mock_requests_get_gfs(*args, **kwargs):
#         """ mock common_model_fetchers download method for GFS """
#         dirname = os.path.dirname(os.path.realpath(__file__))
#         filename = os.path.join(
#             dirname, 'gfs_4_20230219_0600_018.grb2')
#         with open(filename, 'rb') as file:
#             content = file.read()
#         return MockResponse(status_code=200, content=content)
#     monkeypatch.setattr(requests, 'get', mock_requests_get_gfs)


def test_get_nam_model_run_download_urls_for_00_utc():
    # March 2 at 00:00 UTC is equivalent to March 1 in Eastern timezone - should return URL for previous day
    # for the 00 UTC run, there should be 5 urls (for hours 20, 42, 45, 66, 69)
    expected_num_of_urls = 5
    actual_urls = list(noaa.get_nam_model_run_download_urls(datetime(2023, 3, 2, 00, tzinfo=timezone.utc), '00'))
    assert len(actual_urls) == expected_num_of_urls
    assert actual_urls[0] == noaa.NAM_BASE_URL + 'dir=%2Fnam.20230301&file=nam.t00z.awip3220.tm00.grib2&var_APCP=on&var_RH=on&var_TMP=on&var_UGRD=on&var_VGRD=on&lev_surface=on&lev_2_m_above_ground=on&lev_10_m_above_ground=on&subregion=&toplat=60&leftlon=-139&rightlon=-114&bottomlat=48'
    assert actual_urls[-1] == noaa.NAM_BASE_URL + 'dir=%2Fnam.20230301&file=nam.t00z.awip3269.tm00.grib2&var_APCP=on&var_RH=on&var_TMP=on&var_UGRD=on&var_VGRD=on&lev_surface=on&lev_2_m_above_ground=on&lev_10_m_above_ground=on&subregion=&toplat=60&leftlon=-139&rightlon=-114&bottomlat=48'


def test_get_nam_model_run_download_urls_for_06_utc():
    # Feb 15 at 06:00 UTC is still Feb 15 (at 02:00) in Eastern timezone - should return URL for same day
    # for the 06 UTC run, there should be 5 urls (for hours 14, 36, 39, 60, 63)
    expected_num_of_urls = 5
    actual_urls = list(noaa.get_nam_model_run_download_urls(datetime(2023, 2, 15, 6, tzinfo=timezone.utc), '06'))
    assert len(actual_urls) == expected_num_of_urls
    assert actual_urls[0] == noaa.NAM_BASE_URL + \
        'dir=%2Fnam.20230215&file=nam.t06z.awip3214.tm00.grib2&var_APCP=on&var_RH=on&var_TMP=on&var_UGRD=on&var_VGRD=on&lev_surface=on&lev_2_m_above_ground=on&lev_10_m_above_ground=on&subregion=&toplat=60&leftlon=-139&rightlon=-114&bottomlat=48'
    assert actual_urls[1] == noaa.NAM_BASE_URL + 'dir=%2Fnam.20230215&file=nam.t06z.awip3236.tm00.grib2&var_APCP=on&var_RH=on&var_TMP=on&var_UGRD=on&var_VGRD=on&lev_surface=on&lev_2_m_above_ground=on&lev_10_m_above_ground=on&subregion=&toplat=60&leftlon=-139&rightlon=-114&bottomlat=48'
    assert actual_urls[-1] == noaa.NAM_BASE_URL + 'dir=%2Fnam.20230215&file=nam.t06z.awip3263.tm00.grib2&var_APCP=on&var_RH=on&var_TMP=on&var_UGRD=on&var_VGRD=on&lev_surface=on&lev_2_m_above_ground=on&lev_10_m_above_ground=on&subregion=&toplat=60&leftlon=-139&rightlon=-114&bottomlat=48'


def test_get_nam_model_run_download_urls_for_12_utc():
    # March 9 at 12:00 UTC is still March 9 in Eastern timezone - should return URL for same day
    # for the 12 UTC run, there should be 4 urls (for hours 08, 32, 54, 57)
    expected_num_of_urls = 4
    actual_urls = list(noaa.get_nam_model_run_download_urls(datetime(2023, 3, 9, 12, tzinfo=timezone.utc), '12'))
    assert len(actual_urls) == expected_num_of_urls
    assert actual_urls[0] == noaa.NAM_BASE_URL + 'dir=%2Fnam.20230309&file=nam.t12z.awip3208.tm00.grib2&var_APCP=on&var_RH=on&var_TMP=on&var_UGRD=on&var_VGRD=on&lev_surface=on&lev_2_m_above_ground=on&lev_10_m_above_ground=on&subregion=&toplat=60&leftlon=-139&rightlon=-114&bottomlat=48'
    assert actual_urls[1] == noaa.NAM_BASE_URL + 'dir=%2Fnam.20230309&file=nam.t12z.awip3232.tm00.grib2&var_APCP=on&var_RH=on&var_TMP=on&var_UGRD=on&var_VGRD=on&lev_surface=on&lev_2_m_above_ground=on&lev_10_m_above_ground=on&subregion=&toplat=60&leftlon=-139&rightlon=-114&bottomlat=48'
    assert actual_urls[-1] == noaa.NAM_BASE_URL + 'dir=%2Fnam.20230309&file=nam.t12z.awip3257.tm00.grib2&var_APCP=on&var_RH=on&var_TMP=on&var_UGRD=on&var_VGRD=on&lev_surface=on&lev_2_m_above_ground=on&lev_10_m_above_ground=on&subregion=&toplat=60&leftlon=-139&rightlon=-114&bottomlat=48'


def test_get_nam_model_run_download_urls_for_18_utc():
    # Jan 27 at 18:00 UTC is still Jan 27 in Eastern timezone - should return URL for same day
    # for the 18 UTC run, there should be 4 urls (for hours 02, 26, 48, 51)
    expected_num_of_urls = 4
    actual_urls = list(noaa.get_nam_model_run_download_urls(datetime(2023, 1, 27, 18, tzinfo=timezone.utc), '18'))
    assert len(actual_urls) == expected_num_of_urls
    assert actual_urls[0] == noaa.NAM_BASE_URL + 'dir=%2Fnam.20230127&file=nam.t18z.awip3202.tm00.grib2&var_APCP=on&var_RH=on&var_TMP=on&var_UGRD=on&var_VGRD=on&lev_surface=on&lev_2_m_above_ground=on&lev_10_m_above_ground=on&subregion=&toplat=60&leftlon=-139&rightlon=-114&bottomlat=48'
    assert actual_urls[1] == noaa.NAM_BASE_URL + 'dir=%2Fnam.20230127&file=nam.t18z.awip3226.tm00.grib2&var_APCP=on&var_RH=on&var_TMP=on&var_UGRD=on&var_VGRD=on&lev_surface=on&lev_2_m_above_ground=on&lev_10_m_above_ground=on&subregion=&toplat=60&leftlon=-139&rightlon=-114&bottomlat=48'
    assert actual_urls[-1] == noaa.NAM_BASE_URL + 'dir=%2Fnam.20230127&file=nam.t18z.awip3251.tm00.grib2&var_APCP=on&var_RH=on&var_TMP=on&var_UGRD=on&var_VGRD=on&lev_surface=on&lev_2_m_above_ground=on&lev_10_m_above_ground=on&subregion=&toplat=60&leftlon=-139&rightlon=-114&bottomlat=48'


def test_parse_url_for_timestamps_simple():
    """ simple test case for noaa.parse_url_for_timestamps(): model_run_timestamp and prediction_timestamp
    are on the same day """
    url = noaa.NAM_BASE_URL + 'dir=%2Fnam.20230413&file=nam.t12z.awip3206.tm00.grib2&var_APCP=on&var_RH=on&var_TMP=on&var_UGRD=on&var_VGRD=on&lev_surface=on&lev_2_m_above_ground=on&lev_10_m_above_ground=on&subregion=&toplat=60&leftlon=-139&rightlon=-114&bottomlat=48'
    expected_model_run_timestamp = datetime(2023, 4, 13, 12, 0, tzinfo=timezone.utc)
    expected_prediction_timestamp = datetime(2023, 4, 13, 18, 0, tzinfo=timezone.utc)
    actual_model_run_timestamp, actual_prediction_timestamp = noaa.parse_nam_url_for_timestamps(url)
    assert expected_model_run_timestamp == actual_model_run_timestamp
    assert expected_prediction_timestamp == actual_prediction_timestamp


def test_parse_url_for_timestamps_complex():
    """ more complex test case for noaa.parse_url_for_timestamps(): model_run_timestamp and
    prediction_timestamp are on different days """
    url = noaa.NAM_BASE_URL + 'dir=%2Fnam.20230413&file=nam.t18z.awip3227.grib2&var_APCP=on&var_RH=on&var_TMP=on&var_UGRD=on&var_VGRD=on&lev_surface=on&lev_2_m_above_ground=on&lev_10_m_above_ground=on&subregion=&toplat=60&leftlon=-139&rightlon=-114&bottomlat=48'
    expected_model_run_timestamp = datetime(2023, 4, 13, 18, 0, tzinfo=timezone.utc)
    expected_prediction_timestamp = datetime(2023, 4, 14, 21, 0, tzinfo=timezone.utc)
    actual_model_run_timestamp, actual_prediction_timestamp = noaa.parse_nam_url_for_timestamps(url)
    assert expected_model_run_timestamp == actual_model_run_timestamp
    assert expected_prediction_timestamp == actual_prediction_timestamp
