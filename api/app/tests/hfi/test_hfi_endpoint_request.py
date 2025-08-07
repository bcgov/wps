"""
Unit tests for hfi endpoints.
"""

import os
from datetime import date
import pytest
import json
from fastapi.testclient import TestClient
from aiohttp import ClientSession
from pytest_mock import MockerFixture
import app.main
import app.routers.hfi_calc
from wps_shared.tests.common import default_mock_client_get
from app.tests import load_json_file
from wps_shared.db.models.hfi_calc import (
    PlanningWeatherStation,
    FuelType,
    FireCentre,
    PlanningArea,
    HFIRequest,
    FireStartRange,
    FireStartLookup,
)
import wps_shared.db.crud.hfi_calc

from app.tests.utils.mock_jwt_decode_role import MockJWTDecodeWithRole


def _setup_mock(monkeypatch: pytest.MonkeyPatch):
    """Prepare all our mocked out calls."""
    # mock anything that uses aiohttp.ClientSession::get
    monkeypatch.setattr(ClientSession, "get", default_mock_client_get)

    fuel_type_1 = FuelType(
        id=1,
        abbrev="O1B",
        fuel_type_code="O1B",
        description="O1B",
        percentage_conifer=0,
        percentage_dead_fir=0,
    )
    fuel_type_2 = FuelType(
        id=2,
        abbrev="C7B",
        fuel_type_code="C7B",
        description="C7B",
        percentage_conifer=100,
        percentage_dead_fir=0,
    )
    fuel_type_3 = FuelType(
        id=3,
        abbrev="C3",
        fuel_type_code="C3",
        description="C3",
        percentage_conifer=100,
        percentage_dead_fir=0,
    )

    def mock_get_fire_weather_stations(_):
        fire_centre = FireCentre(id=1, name="Kamloops Fire Centre")
        planning_area_1 = PlanningArea(
            id=1, name="Kamloops (K2)", fire_centre_id=1, order_of_appearance_in_list=1
        )
        planning_area_2 = PlanningArea(
            id=2, name="Vernon (K4)", fire_centre_id=1, order_of_appearance_in_list=2
        )
        return [
            (
                PlanningWeatherStation(station_code=230, fuel_type_id=1, planning_area_id=1),
                fuel_type_1,
                planning_area_1,
                fire_centre,
            ),
            (
                PlanningWeatherStation(station_code=239, fuel_type_id=1, planning_area_id=1),
                fuel_type_1,
                planning_area_1,
                fire_centre,
            ),
            (
                PlanningWeatherStation(station_code=230, fuel_type_id=2, planning_area_id=2),
                fuel_type_2,
                planning_area_2,
                fire_centre,
            ),
        ]

    code1 = 230
    code2 = 239
    all_station_codes = [{"station_code": code1}, {"station_code": code2}]

    def mock_get_all_stations(__):
        """Returns mocked WFWXWeatherStations codes."""
        return all_station_codes

    def mock_get_fire_centre_fire_start_ranges(_, __: int):
        """Returns mocked FireStartRange"""
        data = ((1, "0-1"), (2, "1-2"), (3, "2-3"), (4, "3-6"), (5, "6+"))
        return [FireStartRange(id=id, label=range) for id, range in data]

    def mock_get_fire_start_lookup(_):
        """Returns mocked FireStartLookup"""
        data = (
            (1, 1, 1, 1),
            (2, 1, 2, 1),
            (3, 1, 3, 2),
            (4, 1, 4, 3),
            (5, 1, 5, 4),
            (6, 2, 1, 1),
            (7, 2, 2, 1),
            (8, 2, 3, 2),
            (9, 2, 4, 4),
            (10, 2, 5, 5),
            (11, 3, 1, 2),
            (12, 3, 2, 3),
            (13, 3, 3, 4),
            (14, 3, 4, 5),
            (15, 3, 5, 6),
            (16, 4, 1, 3),
            (17, 4, 2, 4),
            (18, 4, 3, 4),
            (19, 4, 4, 5),
            (20, 4, 5, 6),
            (21, 5, 1, 4),
            (22, 5, 2, 5),
            (23, 5, 3, 6),
            (24, 5, 4, 6),
            (25, 5, 5, 6),
        )
        return [
            FireStartLookup(
                id=id,
                fire_start_range_id=fire_start_range_id,
                mean_intensity_group=mean_intensity_group,
                prep_level=prep_level,
            )
            for id, fire_start_range_id, mean_intensity_group, prep_level in data
        ]

    fuel_types = [fuel_type_1, fuel_type_2, fuel_type_3]

    def mock_get_fuel_type_by_id(_, fuel_type_id: int):
        """Returns mocked FuelType"""
        try:
            return next(fuel_type for fuel_type in fuel_types if fuel_type.id == fuel_type_id)
        except StopIteration:
            return None

    def mock_get_fuel_types(_):
        return fuel_types

    def mock_get_most_recent_updated_hfi_request(*arg):
        dirname = os.path.dirname(os.path.realpath(__file__))
        filename = os.path.join(dirname, "test_hfi_endpoint_request.json")
        with open(filename) as f:
            request = json.dumps(json.load(f))
            return HFIRequest(
                fire_centre_id=1,
                prep_start_day=date(2020, 5, 21),
                prep_end_day=date(2020, 5, 25),
                request=request,
            )

    monkeypatch.setattr(
        app.hfi.hfi_calc, "get_fire_weather_stations", mock_get_fire_weather_stations
    )
    monkeypatch.setattr(wps_shared.db.crud.hfi_calc, "get_all_stations", mock_get_all_stations)
    monkeypatch.setattr(
        app.hfi.hfi_calc,
        "get_fire_centre_fire_start_ranges",
        mock_get_fire_centre_fire_start_ranges,
    )
    monkeypatch.setattr(app.hfi.hfi_calc, "get_fuel_types", mock_get_fuel_types)
    monkeypatch.setattr(app.hfi.hfi_calc, "get_fire_start_lookup", mock_get_fire_start_lookup)
    monkeypatch.setattr(app.routers.hfi_calc, "get_fuel_type_by_id", mock_get_fuel_type_by_id)
    monkeypatch.setattr(app.routers.hfi_calc, "crud_get_fuel_types", mock_get_fuel_types)
    monkeypatch.setattr(
        app.routers.hfi_calc,
        "get_most_recent_updated_hfi_request_for_current_date",
        mock_get_most_recent_updated_hfi_request,
    )
    monkeypatch.setattr(
        app.routers.hfi_calc,
        "get_most_recent_updated_hfi_request",
        mock_get_most_recent_updated_hfi_request,
    )


def _setup_mock_with_role(monkeypatch: pytest.MonkeyPatch, role: str):
    """Prepare jwt decode to be mocked with permission"""
    _setup_mock(monkeypatch)

    def mock_fire_start_role_function(*args, **kwargs):
        return MockJWTDecodeWithRole(role)

    if role != "None":
        monkeypatch.setattr("jwt.decode", mock_fire_start_role_function)


headers = {"Content-Type": "application/json", "Authorization": "Bearer token"}


@pytest.mark.parametrize(
    "url, status_code, response_json, request_saved, stored_request_json",
    [
        ("/api/hfi-calc/fire_centre/1", 200, "test_hfi_endpoint_load_response.json", False, None),
        (
            "/api/hfi-calc/fire_centre/1",
            200,
            "test_hfi_endpoint_load_response.json",
            False,
            "test_hfi_endpoint_stored_request.json",
        ),
        (
            "/api/hfi-calc/fire_centre/1/2020-05-21/2020-05-25",
            200,
            "test_hfi_endpoint_load_response.json",
            False,
            None,
        ),
        (
            "/api/hfi-calc/fire_centre/1/2020-05-21/2020-05-25",
            200,
            "test_hfi_endpoint_load_response.json",
            False,
            "test_hfi_endpoint_stored_request.json",
        ),
        # pdf
        ("api/hfi-calc/fire_centre/1/2020-05-21/2020-05-25/pdf", 200, None, False, None),
        (
            "api/hfi-calc/fire_centre/1/2020-05-21/2020-05-25/pdf",
            200,
            None,
            False,
            "test_hfi_endpoint_stored_request.json",
        ),
    ],
)
@pytest.mark.usefixtures("mock_jwt_decode")
def test_hfi_get_request(
    url,
    status_code,
    response_json,
    request_saved,
    stored_request_json,
    monkeypatch,
    mocker: MockerFixture,
):
    """Request endpoints and verify responses"""
    _setup_mock(monkeypatch)
    spy_store_hfi_request = mocker.spy(app.routers.hfi_calc, "store_hfi_request")

    expected_response = load_json_file(__file__)(response_json)

    client = TestClient(app.main.app)
    response = client.get(url, headers=headers)
    assert response.status_code == status_code
    assert spy_store_hfi_request.called == request_saved
    if expected_response is not None:
        assert response.json() == expected_response


@pytest.mark.parametrize(
    "url, role, status_code, response_json, request_saved, stored_request_json",
    [
        # Test the station selection with correct role
        (
            "/api/hfi-calc/fire_centre/1/2020-05-21/2020-05-25/planning_area/1/fire_starts/2020-05-21/fire_start_range/2",
            "hfi_set_fire_starts",
            200,
            "test_hfi_endpoint_response_set_fire_start_range.json",
            True,
            None,
        ),
        (
            "/api/hfi-calc/fire_centre/1/2020-05-21/2020-05-25/planning_area/1/fire_starts/2020-05-21/fire_start_range/2",
            "hfi_set_fire_starts",
            200,
            "test_hfi_endpoint_response_set_fire_start_range.json",
            True,
            "test_hfi_endpoint_stored_request.json",
        ),
        (
            "/api/hfi-calc/fire_centre/1/2020-05-21/2020-05-25/planning_area/1/station/230/selected/false",
            "hfi_select_station",
            200,
            "test_hfi_endpoint_response_deselect_station.json",
            True,
            None,
        ),
        (
            "/api/hfi-calc/fire_centre/1/2020-05-21/2020-05-25/planning_area/1/station/230/selected/false",
            "hfi_select_station",
            200,
            "test_hfi_endpoint_response_deselect_station.json",
            True,
            "test_hfi_endpoint_stored_request.json",
        ),
        (
            "/api/hfi-calc/fire_centre/1/2020-05-21/2020-05-25/planning_area/1/station/230/selected/true",
            "hfi_select_station",
            200,
            "test_hfi_endpoint_response_select_station.json",
            True,
            None,
        ),
        (
            "/api/hfi-calc/fire_centre/1/2020-05-21/2020-05-25/planning_area/1/station/230/selected/true",
            "hfi_select_station",
            200,
            "test_hfi_endpoint_response_select_station.json",
            True,
            "test_hfi_endpoint_stored_request.json",
        ),
        # Test the station selection without roles
        (
            "/api/hfi-calc/fire_centre/1/2020-05-21/2020-05-25/planning_area/1/station/230/fuel_type/2",
            "hfi_set_fuel_type",
            200,
            "test_hfi_endpoint_response_set_fuel_type.json",
            True,
            None,
        ),
        (
            "/api/hfi-calc/fire_centre/1/2020-05-21/2020-05-25/planning_area/1/station/230/fuel_type/2",
            "hfi_set_fuel_type",
            200,
            "test_hfi_endpoint_response_set_fuel_type.json",
            True,
            "test_hfi_endpoint_stored_request.json",
        ),
        # Invalid fuel type should return 500 error, and not be saved.
        (
            "/api/hfi-calc/fire_centre/1/2020-05-21/2020-05-25/planning_area/1/station/230/fuel_type/-1",
            "hfi_set_fuel_type",
            500,
            None,
            False,
            None,
        ),
    ],
)
def test_hfi_post_request(
    url,
    role,
    status_code,
    response_json,
    request_saved,
    stored_request_json,
    monkeypatch,
    mocker: MockerFixture,
):
    """Request endpoints and verify responses"""
    _setup_mock_with_role(monkeypatch, role)
    spy_store_hfi_request = mocker.spy(app.routers.hfi_calc, "store_hfi_request")

    expected_response = load_json_file(__file__)(response_json) if response_json else None

    client = TestClient(app.main.app)
    response = client.post(url, headers=headers)
    assert spy_store_hfi_request.called == request_saved
    assert response.status_code == status_code
    if expected_response is not None:
        assert response.json() == expected_response
