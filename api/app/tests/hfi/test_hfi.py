""" Unit testing for hfi logic """
from datetime import datetime

from pytest_mock import MockerFixture
from app.db.database import get_read_session_scope
from app.hfi.hfi import (calculate_hfi_results,
                         calculate_mean_intensity,
                         calculate_max_intensity_group,
                         calculate_prep_level, validate_station_daily)
import app.db.models.hfi_calc as hfi_calc_models
from app.schemas.hfi_calc import (FireCentre,
                                  PlanningArea,
                                  StationDaily,
                                  WeatherStation,
                                  WeatherStationProperties,
                                  required_daily_fields,
                                  lowest_fire_starts,
                                  one_2_two_starts,
                                  two_2_three_starts,
                                  three_2_six_starts,
                                  highest_fire_starts,
                                  all_ranges)
from app.schemas.shared import FuelType

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
                        fuel_type=FuelType(abbrev="C1", description="", fuel_type_code="C1", percentage_conifer=100, percentage_dead_fir=0))),
            WeatherStation(
                code=2,
                station_props=WeatherStationProperties(
                    wfwx_station_uuid='2',
                    name="station2",
                    elevation=1,
                    fuel_type=FuelType(abbrev="C1", description="", fuel_type_code="C1", percentage_conifer=100, percentage_dead_fir=0)))
        ]
    )
    ]
)


def test_no_dailies_handled():
    """ No dailies are handled """
    result = calculate_hfi_results(planning_area_fire_starts={},
                                   dailies=[],
                                   num_prep_days=5,
                                   selected_station_codes=[1, 2],
                                   area_station_map={},
                                   start_date=datetime.now())

    assert result == []


def test_requested_fire_starts_unaltered(mocker: MockerFixture):
    """ Fire starts from user request remain unchanged """

    start_date = datetime.now()
    daily = StationDaily(
        code=1,
        date=start_date,
        intensity_group=1
    )

    station = hfi_calc_models.PlanningWeatherStation(id=1, planning_area_id=1, station_code=1)

    result = calculate_hfi_results(planning_area_fire_starts={
        kamloops_fc.planning_areas[0].id: [highest_fire_starts]},
        dailies=[daily],
        num_prep_days=5,
        selected_station_codes=[1, 2],
        area_station_map={kamloops_fc.planning_areas[0].id: [station]},
        start_date=start_date)
    assert result[0].daily_results[0].fire_starts == highest_fire_starts


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
    result = calculate_mean_intensity([daily1, daily2])
    assert result == 1


def test_calculate_mean_intensity_empty():
    """ Calculates mean intensity with empty list """
    result = calculate_mean_intensity([])
    assert result == None


def test_max_mean_intensity_basic():
    """ Calculates max mean intensity of basic case """
    result = calculate_max_intensity_group([1, 2])
    assert result == 2


def test_max_mean_intensity_empty():
    """ Calculates max mean intensity with empty list """
    result = calculate_max_intensity_group([])
    assert result == None


def test_calculate_prep_level_empty():
    """ Calculates prep level of empty case """
    for fire_start_range in all_ranges:
        result = calculate_prep_level(None, fire_start_range)
        assert result == None


def test_lowest_prep_level():
    """ Calculates prep level of lowest fire start range """
    assert calculate_prep_level(1, lowest_fire_starts) == 1
    assert calculate_prep_level(2, lowest_fire_starts) == 1
    assert calculate_prep_level(3, lowest_fire_starts) == 2
    assert calculate_prep_level(4, lowest_fire_starts) == 3
    assert calculate_prep_level(5, lowest_fire_starts) == 4


def test_1_2_prep_level():
    """ Calculates prep level for 1-2 fire starts """
    assert calculate_prep_level(1, one_2_two_starts) == 1
    assert calculate_prep_level(2, one_2_two_starts) == 2
    assert calculate_prep_level(3, one_2_two_starts) == 3
    assert calculate_prep_level(4, one_2_two_starts) == 4
    assert calculate_prep_level(5, one_2_two_starts) == 5


def test_2_3_prep_level():
    """ Calculates prep level for 2-3 fire starts """
    assert calculate_prep_level(1, two_2_three_starts) == 2
    assert calculate_prep_level(2, two_2_three_starts) == 3
    assert calculate_prep_level(3, two_2_three_starts) == 4
    assert calculate_prep_level(4, two_2_three_starts) == 5
    assert calculate_prep_level(5, two_2_three_starts) == 6


def test_3_6_prep_level():
    """ Calculates prep level for 3-6 fire starts """
    assert calculate_prep_level(1, three_2_six_starts) == 3
    assert calculate_prep_level(2, three_2_six_starts) == 4
    assert calculate_prep_level(3, three_2_six_starts) == 5
    assert calculate_prep_level(4, three_2_six_starts) == 6
    assert calculate_prep_level(5, three_2_six_starts) == 6


def test_highest_prep_level():
    """ Calculates prep level for 6+ fire starts """
    assert calculate_prep_level(1, highest_fire_starts) == 4
    assert calculate_prep_level(2, highest_fire_starts) == 5
    assert calculate_prep_level(3, highest_fire_starts) == 6
    assert calculate_prep_level(4, highest_fire_starts) == 6
    assert calculate_prep_level(5, highest_fire_starts) == 6


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
