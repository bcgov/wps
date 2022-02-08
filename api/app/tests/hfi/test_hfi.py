""" Unit testing for hfi logic """
from datetime import datetime
from app.hfi.hfi import calculate_hfi_results
from app.schemas.hfi_calc import FireCentre, PlanningArea, StationDaily, WeatherStation, WeatherStationProperties, highest_fire_starts
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
        status=None,
        temperature=None,
        relative_humidity=None,
        wind_speed=None,
        wind_direction=None,
        grass_cure_percentage=None,
        precipitation=None,
        ffmc=None,
        dmc=None,
        dc=None,
        isi=None,
        bui=None,
        fwi=None,
        danger_class=None,
        observation_valid=None,
        observation_valid_comment=None,
        rate_of_spread=None,
        hfi=None,
        intensity_group=1,
        sixty_minute_fire_size=None,
        fire_type=None,
        error=None,
        error_message=None,
        last_updated=None
    )
    result = calculate_hfi_results(fire_centre=kamloops_fc,
                                   planning_area_fire_starts={
                                       kamloops_fc.planning_areas[0].name: [highest_fire_starts]},
                                   dailies=[daily],
                                   num_prep_days=5,
                                   selected_station_codes=[1, 2])
    assert result[kamloops_fc.planning_areas[0].name].daily_results[0].fire_starts == highest_fire_starts
