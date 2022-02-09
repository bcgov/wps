""" Unit testing for hfi logic """
from datetime import datetime
from app.hfi.hfi import (calculate_hfi_results,
                         calculate_mean_intensity,
                         calculate_max_intensity_group,
                         calculate_prep_level)
from app.schemas.hfi_calc import (FireCentre,
                                  PlanningArea,
                                  StationDaily,
                                  WeatherStation,
                                  WeatherStationProperties,
                                  highest_fire_starts,
                                  all_ranges)
from app.schemas.shared import FuelType

# Kamloops FC fixture
kamloops_fc = FireCentre(
    name='Kamloops',
    planning_areas=[PlanningArea(
        name="Vernon",
        order_of_appearance_in_list=None,
        stations=[
            WeatherStation(
                    code=1,
                    station_props=WeatherStationProperties(
                        wfwx_station_uuid='1',
                        name="station1",
                        elevation=1,
                        fuel_type=FuelType(abbrev="C1", description=""))),
            WeatherStation(
                code=2,
                station_props=WeatherStationProperties(
                    wfwx_station_uuid='2',
                    name="station2",
                    elevation=1,
                    fuel_type=FuelType(abbrev="C1", description="")))
        ]
    )
    ]
)


def test_empty_map_without_fire_centre():
    """ No fire centre returns empty result """
    result = calculate_hfi_results(fire_centre=None,
                                   planning_area_fire_starts={},
                                   dailies=[],
                                   num_prep_days=5,
                                   selected_station_codes=[])
    assert result == {}


def test_no_dailies_handled():
    """ No dailies are handled """
    result = calculate_hfi_results(fire_centre=kamloops_fc,
                                   planning_area_fire_starts={},
                                   dailies=[],
                                   num_prep_days=5,
                                   selected_station_codes=[1, 2])
    assert result != {}


def test_requested_fire_starts_unaltered():
    """ Fire starts from user request remain unchanged """
    daily = StationDaily(
        code=1,
        date=datetime.now(),
        intensity_group=1
    )
    result = calculate_hfi_results(fire_centre=kamloops_fc,
                                   planning_area_fire_starts={
                                       kamloops_fc.planning_areas[0].name: [highest_fire_starts]},
                                   dailies=[daily],
                                   num_prep_days=5,
                                   selected_station_codes=[1, 2])
    assert result[kamloops_fc.planning_areas[0].name].daily_results[0].fire_starts == highest_fire_starts


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
