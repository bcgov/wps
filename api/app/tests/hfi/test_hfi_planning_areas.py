import pytest
from starlette.testclient import TestClient
from sqlalchemy.orm import Session
import app.main
from common.db.models.hfi_calc import PlanningWeatherStation, FireCentre, FuelType, PlanningArea
import app.routers.hfi_calc


def mock_get_fire_weather_stations(_: Session):
    fire_centre = FireCentre(id=1, name="Kamloops Fire Centre")
    planning_area_1 = PlanningArea(id=2, name="Kamloops (K2)", fire_centre_id=1)
    planning_area_2 = PlanningArea(id=3, name="Vernon (K4)", fire_centre_id=1)
    fuel_type_1 = FuelType(id=1, abbrev="O1B", description="neigh", fuel_type_code="O1B", percentage_conifer=0, percentage_dead_fir=0)
    fuel_type_2 = FuelType(id=2, abbrev="C7B", description="moo", fuel_type_code="C7", percentage_conifer=100, percentage_dead_fir=0)
    return (
        (PlanningWeatherStation(station_code=322, fuel_type_id=1, planning_area_id=1), fuel_type_1, planning_area_1, fire_centre),
        (PlanningWeatherStation(station_code=346, fuel_type_id=2, planning_area_id=2), fuel_type_2, planning_area_2, fire_centre),
        (PlanningWeatherStation(station_code=334, fuel_type_id=2, planning_area_id=2), fuel_type_2, planning_area_2, fire_centre),
    )


@pytest.mark.usefixtures("mock_client_session", "mock_jwt_decode")
def test_get_fire_weather_stations(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(app.hfi.hfi_calc, "get_fire_weather_stations", mock_get_fire_weather_stations)
    client = TestClient(app.main.app)
    headers = {"Content-Type": "application/json", "Authorization": "Bearer token"}
    response = client.get("/api/hfi-calc/fire-centres/", headers=headers)

    """ Assert that we receive the minimum expected number of fire centres """
    assert len(response.json()["fire_centres"]) >= 1

    """ Assert that each fire centre returned has at least 1 planning area assigned to it """
    for fire_centre in response.json()["fire_centres"]:
        assert len(fire_centre['planning_areas']) >= 1

    for fire_centre in response.json()["fire_centres"]:
        for planning_area in fire_centre['planning_areas']:
            assert len(planning_area['stations']) >= 1
