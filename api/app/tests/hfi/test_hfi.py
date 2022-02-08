""" Unit testing for hfi logic """
from app.hfi.hfi import calculate_hfi_results
from app.schemas.hfi_calc import FireCentre, PlanningArea, WeatherStation, WeatherStationProperties
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


def test_basic_calculate():
    """ Basic result """
    result = calculate_hfi_results(fire_centre=kamloops_fc,
                                   planning_area_fire_starts={},
                                   dailies=[],
                                   num_prep_days=5,
                                   selected_station_codes=[1, 2])
    assert result != {}
