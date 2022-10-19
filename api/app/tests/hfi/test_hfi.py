""" Unit testing for hfi logic """
from datetime import date, datetime, timedelta
import pytest
import os
import json
from pytest_mock import MockerFixture
from app.hfi.hfi_calc import (calculate_hfi_results,
                              calculate_mean_intensity,
                              calculate_max_intensity_group,
                              calculate_prep_level,
                              validate_date_range,
                              validate_station_daily)
import app.db.models.hfi_calc as hfi_calc_models
from app.schemas.hfi_calc import (DateRange,
                                  FireCentre,
                                  FireStartRange,
                                  InvalidDateRangeError,
                                  PlanningArea,
                                  StationDaily, StationInfo,
                                  WeatherStation,
                                  WeatherStationProperties,
                                  required_daily_fields)
from app.schemas.shared import FuelType
from app.utils.time import get_pst_now, get_utc_now
from app.wildfire_one.schema_parsers import WFWXWeatherStation
from starlette.testclient import TestClient
from app.main import app as starlette_app
import app.routers.hfi_calc

# Kamloops FC fixture
kamloops_fc = FireCentre(
    id=1,
    name='Kamloops',
    planning_areas=[PlanningArea(
        id=1,
        name="Vernon",
        order_of_appearance_in_list=None,
        stations=[
            WeatherStation(
                    code=1,
                    station_props=WeatherStationProperties(
                        wfwx_station_uuid='1',
                        name="station1",
                        elevation=1,
                    )),
            WeatherStation(
                code=2,
                station_props=WeatherStationProperties(
                    wfwx_station_uuid='2',
                    name="station2",
                    elevation=1,
                ))
        ]
    )
    ]
)


fire_start_ranges = [FireStartRange(label='moo', id=1), FireStartRange(label='moo', id=2)]
fire_start_lookup = {1: {1: 1}, 2: {1: 1}}

planning_area_station_info = {kamloops_fc.planning_areas[0].id: [
    StationInfo(station_code=1, selected=True, fuel_type_id=1),
    StationInfo(station_code=2, selected=True, fuel_type_id=1)
]}


def test_no_dailies_handled():
    """ No dailies are handled """
    result = calculate_hfi_results({},
                                   fire_start_ranges,
                                   planning_area_fire_starts={},
                                   fire_start_lookup=fire_start_lookup,
                                   wfwx_stations=[],
                                   raw_dailies=[],
                                   num_prep_days=5,
                                   planning_area_station_info=planning_area_station_info,
                                   area_station_map={},
                                   start_date=datetime.now())

    assert result == []


def test_requested_fire_starts_unaltered(mocker: MockerFixture):
    """ Fire starts from user request remain unchanged """

    start_date = datetime.now()
    station = hfi_calc_models.PlanningWeatherStation(id=1, planning_area_id=1, station_code=1)
    fuel_type_lookup = {
        1: hfi_calc_models.FuelType(
            id=1, abbrev='C1', description='C1', fuel_type_code='C1',
            percentage_conifer=100, percentage_dead_fir=0)}
    planning_area_fire_starts = {
        kamloops_fc.planning_areas[0].id: [fire_start_ranges[-1]]}
    wfwx_station = WFWXWeatherStation(
        wfwx_id=1, code=1, name='station1', latitude=12.1,
        longitude=12.1, elevation=123, zone_code=1)
    raw_daily = {
        'stationId': 1,
        'weatherTimestamp': get_utc_now().timestamp() * 1000,
        'lastEntityUpdateTimestamp': get_utc_now().timestamp() * 1000
    }

    result = calculate_hfi_results(fuel_type_lookup,
                                   fire_start_ranges,
                                   planning_area_fire_starts=planning_area_fire_starts,
                                   fire_start_lookup=fire_start_lookup,
                                   wfwx_stations=[wfwx_station],
                                   raw_dailies=[
                                       raw_daily],
                                   num_prep_days=5,
                                   planning_area_station_info=planning_area_station_info,
                                   area_station_map={kamloops_fc.planning_areas[0].id: [station]},
                                   start_date=start_date)
    assert result[0].daily_results[0].fire_starts == fire_start_ranges[-1]


def test_calculate_mean_intensity_basic():
    """ Calculates mean intensity """
    daily1 = StationDaily(
        code=1,
        date=datetime.now(),
        intensity_group=1
    )

    daily2 = StationDaily(
        code=2,
        date=datetime.now(),
        intensity_group=1
    )
    result = calculate_mean_intensity([daily1, daily2], 2)
    assert result == 1


def test_calculate_mean_intensity_empty():
    """ Calculates mean intensity with empty list """
    result = calculate_mean_intensity([], 0)
    assert result == None


def test_calculate_mean_intensity_round_down():
    """ Calculates mean intensity and rounds result down because decimal is below x.8 """
    daily1 = StationDaily(code=1, date=datetime.now(), intensity_group=1)
    daily2 = StationDaily(code=2, date=datetime.now(), intensity_group=3)
    daily3 = StationDaily(code=3, date=datetime.now(), intensity_group=4)
    # mean is 2.66666667
    result = calculate_mean_intensity([daily1, daily2, daily3], 3)
    assert result == 2


def test_calculate_mean_intensity_round_up():
    """ Calculates mean intensity and rounds result up because decimal is at x.8 """
    daily1 = StationDaily(code=1, date=datetime.now(), intensity_group=2)
    daily2 = StationDaily(code=2, date=datetime.now(), intensity_group=4)
    daily3 = StationDaily(code=3, date=datetime.now(), intensity_group=4)
    daily4 = StationDaily(code=4, date=datetime.now(), intensity_group=4)
    daily5 = StationDaily(code=5, date=datetime.now(), intensity_group=5)
    # mean is 3.8
    result = calculate_mean_intensity([daily1, daily2, daily3, daily4, daily5], 5)
    assert result == 4


def test_calculate_mean_intensity_round_up_2():
    """ Calculates mean intensity and rounds result up because decimal is above x.8 """
    daily1 = StationDaily(code=1, date=datetime.now(), intensity_group=2)
    daily2 = StationDaily(code=2, date=datetime.now(), intensity_group=4)
    daily3 = StationDaily(code=3, date=datetime.now(), intensity_group=4)
    daily4 = StationDaily(code=4, date=datetime.now(), intensity_group=4)
    daily5 = StationDaily(code=5, date=datetime.now(), intensity_group=4)
    daily6 = StationDaily(code=6, date=datetime.now(), intensity_group=5)
    # mean is 3.83
    result = calculate_mean_intensity([daily1, daily2, daily3, daily4, daily5, daily6], 6)
    assert result == 4


def test_calculate_mean_intensity_perfect_divisor():
    """ Calculates mean intensity, shouldn't need to round """
    daily1 = StationDaily(code=1, date=datetime.now(), intensity_group=2)
    daily2 = StationDaily(code=2, date=datetime.now(), intensity_group=2)
    result = calculate_mean_intensity([daily1, daily2], 2)
    assert result == 2


def test_max_mean_intensity_basic():
    """ Calculates max mean intensity of basic case """
    result = calculate_max_intensity_group([1, 2])
    assert result == 2


def test_max_mean_intensity_empty():
    """ Calculates max mean intensity with empty list """
    result = calculate_max_intensity_group([])
    assert result == None


def test_max_mean_intensity_with_none():
    """ Calculates max mean intensity when we don't have values for all days """
    result = calculate_max_intensity_group([1, None, 2])
    assert result == 2


def test_calculate_prep_level_empty():
    """ Calculates prep level of empty case """
    assert calculate_prep_level(None, FireStartRange(id=1, label='blah'), None) == None


def test_valid_daily():
    """ Daily with all required fields is valid """
    daily = StationDaily(
        code=1,
        date=datetime.now(),
        temperature=1,
        relative_humidity=1,
        wind_speed=1,
        wind_direction=1,
        precipitation=1,
        intensity_group=1
    )
    result = validate_station_daily(daily)
    assert result.valid == True


def test_valid_daily():
    """ Daily missing any required field is invalid """
    base_daily = StationDaily(
        code=1,
        date=datetime.now(),
        temperature=1,
        relative_humidity=1,
        wind_speed=1,
        wind_direction=1,
        precipitation=1,
        intensity_group=1
    )
    for field in required_daily_fields:
        daily = StationDaily(**base_daily.__dict__)
        setattr(daily, field, None)
        result = validate_station_daily(daily)
        assert result.valid == False


@pytest.mark.usefixtures("mock_jwt_decode")
def test_valid_fuel_types_response(monkeypatch):
    """ Assert that list of FuelType objects is converted to FuelTypesResponse object correctly """
    def mock_get_fuel_types(*args, **kwargs):
        fuel_type_1 = FuelType(id=1, abbrev="T1", fuel_type_code="T1", description="blah",
                               percentage_conifer=0, percentage_dead_fir=0)
        fuel_type_2 = FuelType(id=2, abbrev="T2", fuel_type_code="T2", description="bleep",
                               percentage_conifer=0, percentage_dead_fir=0)
        fuel_type_3 = FuelType(id=3, abbrev="T3", fuel_type_code="T3", description="bloop",
                               percentage_conifer=0, percentage_dead_fir=0)
        return [fuel_type_1, fuel_type_2, fuel_type_3]

    monkeypatch.setattr(app.routers.hfi_calc, 'crud_get_fuel_types', mock_get_fuel_types)
    correct_response_file = os.path.join(os.path.dirname(__file__), 'test_valid_fuel_types_response.json')

    client = TestClient(starlette_app)
    response = client.get('/api/hfi-calc/fuel_types')
    assert response.status_code == 200
    assert response.headers['content-type'] == 'application/json'
    with open(correct_response_file) as file_reader:
        assert response.json() == json.loads(file_reader.read())


def test_valid_date_range_none():
    """ Today to today+5 days is default range when input range is None (start inclusive, end exclusive) """
    result = validate_date_range(None)
    assert result.start_date.isoformat() == '2020-05-21'
    assert result.end_date.isoformat() == '2020-05-25'


def test_valid_date_range_7_days():
    """ 7 day range is acceptable (start inclusive, end exclusive) """
    start_date = get_pst_now()
    end_date = start_date + timedelta(days=7)
    result = validate_date_range(DateRange(start_date=start_date, end_date=end_date))
    assert result.start_date.isoformat() == '2020-05-21'
    assert result.end_date.isoformat() == '2020-05-27'


def test_valid_date_range_over_7_days():
    """ Over 7 days is clamped to 5 days (start inclusive, end exclusive) """
    start_date = get_pst_now()
    end_date = start_date + timedelta(days=8)
    result = validate_date_range(DateRange(start_date=start_date, end_date=end_date))
    assert result.start_date.isoformat() == '2020-05-21'
    assert result.end_date.isoformat() == '2020-05-27'


def test_valid_date_range_over_at_least_one_day():
    """ 1 day range is acceptable (start inclusive, end exclusive) """
    start_date = get_pst_now()
    end_date = start_date
    result = validate_date_range(DateRange(start_date=start_date, end_date=end_date))
    assert result.start_date.isoformat() == '2020-05-21'
    assert result.end_date.isoformat() == '2020-05-21'


def test_valid_date_range_default_for_end_date_before():
    """ If end date is before start date, set it to same day as start date (start inclusive, end exclusive) """
    start_date = get_pst_now()
    end_date = start_date - timedelta(days=1)
    result = validate_date_range(DateRange(start_date=start_date, end_date=end_date))
    assert result.start_date.isoformat() == '2020-05-21'
    assert result.end_date.isoformat() == '2020-05-21'


def test_inclusive_date_math():
    """ Test the the number of days in a date range is calculated correctly. """
    assert DateRange(start_date=date(2020, 5, 21), end_date=date(2020, 5, 25)).days_in_range() == 5
    assert DateRange(start_date=date(2020, 5, 21), end_date=date(2020, 5, 21)).days_in_range() == 1


def test_inclusive_date_math_bad_start_date():
    """ Test that range calculation doesn't raise exception with invalid end date. """
    with pytest.raises(InvalidDateRangeError):
        DateRange(start_date=date(2020, 5, 26), end_date=date(2020, 5, 25)).days_in_range()
