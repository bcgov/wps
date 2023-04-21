""" Unit tests for app/jobs/noaa.py """

import logging
from datetime import datetime, timezone
from app.jobs import noaa


logger = logging.getLogger(__name__)


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
