from unittest.mock import patch
import math
import pytest
from fastapi.testclient import TestClient
from datetime import date, datetime, timezone
from collections import namedtuple
from common.db.models.auto_spatial_advisory import AdvisoryTPIStats, HfiClassificationThreshold, RunParameters, SFMSFuelType, TPIFuelArea, TPIClassEnum

mock_fire_centre_name = "PGFireCentre"

get_fire_centres_url = "/api/fba/fire-centers"
get_fire_zone_areas_url = "/api/fba/fire-shape-areas/forecast/2022-09-27/2022-09-27"
get_fire_zone_tpi_stats_url = "/api/fba/fire-zone-tpi-stats/forecast/2022-09-27/2022-09-27/1"
get_fire_centre_info_url = "/api/fba/fire-centre-hfi-stats/forecast/2022-09-27/2022-09-27/Kamloops%20Fire%20Centre"
get_fire_centre_tpi_stats_url = f"/api/fba/fire-centre-tpi-stats/forecast/2024-08-10/2024-08-10/{mock_fire_centre_name}"
get_sfms_run_datetimes_url = "/api/fba/sfms-run-datetimes/forecast/2022-09-27"

decode_fn = "jwt.decode"
mock_tpi_stats = AdvisoryTPIStats(id=1, advisory_shape_id=1, valley_bottom=1, mid_slope=2, upper_slope=3, pixel_size_metres=50)
mock_tpi_fuel_area_1 = TPIFuelArea(id=1, advisory_shape_id=1, tpi_class=TPIClassEnum.valley_bottom, fuel_area=1)
mock_tpi_fuel_area_2 = TPIFuelArea(id=2, advisory_shape_id=1, tpi_class=TPIClassEnum.mid_slope, fuel_area=2)
mock_tpi_fuel_area_3 = TPIFuelArea(id=3, advisory_shape_id=1, tpi_class=TPIClassEnum.upper_slope, fuel_area=3)
mock_tpi_fuel_areas = [mock_tpi_fuel_area_1, mock_tpi_fuel_area_2, mock_tpi_fuel_area_3]
mock_fire_centre_info = [(9.0, 11.0, 1, 1, 50, 100)]
mock_sfms_run_datetimes = [
    RunParameters(id=1, run_type="forecast", run_datetime=datetime(year=2024, month=1, day=1, hour=1, tzinfo=timezone.utc), for_date=date(year=2024, month=1, day=2))
]

CentreHFIFuelResponse = namedtuple("CentreHFIFuelResponse", ["advisory_shape_id", "source_identifier", "valley_bottom", "mid_slope", "upper_slope", "pixel_size_metres"])
mock_centre_tpi_stats_1 = CentreHFIFuelResponse(advisory_shape_id=1, source_identifier=1, valley_bottom=1, mid_slope=2, upper_slope=3, pixel_size_metres=2)
mock_centre_tpi_stats_2 = CentreHFIFuelResponse(advisory_shape_id=2, source_identifier=2, valley_bottom=1, mid_slope=2, upper_slope=3, pixel_size_metres=2)

CentreTPIFuelAreasResponse = namedtuple("CentreTPIFuelAreasResponse", ["tpi_class", "fuel_area", "source_identifier"])
mock_centre_tpi_fuel_area_1 = CentreTPIFuelAreasResponse(tpi_class=TPIClassEnum.valley_bottom, fuel_area=1, source_identifier=1)
mock_centre_tpi_fuel_area_2 = CentreTPIFuelAreasResponse(tpi_class=TPIClassEnum.mid_slope, fuel_area=2, source_identifier=1)
mock_centre_tpi_fuel_area_3 = CentreTPIFuelAreasResponse(tpi_class=TPIClassEnum.upper_slope, fuel_area=3, source_identifier=1)


async def mock_get_fire_centres(*_, **__):
    return []


async def mock_get_hfi_area(*_, **__):
    return []


async def mock_get_auth_header(*_, **__):
    return {}


async def mock_get_tpi_stats(*_, **__):
    return mock_tpi_stats

async def mock_get_fire_zone_tpi_fuel_areas(*_, **__):
    return mock_tpi_fuel_areas


async def mock_get_tpi_stats_none(*_, **__):
    return None


async def mock_get_fire_zone_tpi_fuel_areas_none(*_, **__):
    return []


async def mock_get_fire_centre_info(*_, **__):
    return mock_fire_centre_info


async def mock_get_centre_tpi_stats(*_, **__):
    return [mock_centre_tpi_stats_1, mock_centre_tpi_stats_2]


async def mock_get_fire_centre_tpi_fuel_areas(*_, **__):
    return [mock_centre_tpi_fuel_area_1, mock_centre_tpi_fuel_area_2, mock_centre_tpi_fuel_area_3]


async def mock_get_sfms_run_datetimes(*_, **__):
    return mock_sfms_run_datetimes


@pytest.fixture()
def client():
    from app.main import app as test_app

    with TestClient(test_app) as test_client:
        yield test_client


@pytest.mark.parametrize(
    "endpoint",
    [get_fire_centres_url, get_fire_zone_areas_url, get_fire_zone_tpi_stats_url, get_fire_centre_info_url, get_sfms_run_datetimes_url],
)
def test_get_endpoints_unauthorized(client: TestClient, endpoint: str):
    """Forbidden to get fire zone areas when unauthorized"""

    response = client.get(endpoint)
    assert response.status_code == 401


@patch("app.routers.fba.get_auth_header", mock_get_auth_header)
@patch("app.routers.fba.get_fire_centers", mock_get_fire_centres)
@pytest.mark.usefixtures("mock_jwt_decode")
def test_get_fire_centres_authorized(client: TestClient):
    """Allowed to get fire centres when authorized"""
    response = client.get(get_fire_centres_url)
    assert response.status_code == 200


async def mock_hfi_thresholds(*_, **__):
    return [HfiClassificationThreshold(id=1, description="4000 < hfi < 10000", name="advisory")]


async def mock_sfms_fuel_types(*_, **__):
    return [SFMSFuelType(id=1, fuel_type_id=1, fuel_type_code="C2", description="test fuel type c2")]


async def mock_zone_ids_in_centre(*_, **__):
    return [1]


@patch("app.routers.fba.get_auth_header", mock_get_auth_header)
@patch("app.routers.fba.get_precomputed_stats_for_shape", mock_get_fire_centre_info)
@patch("app.routers.fba.get_all_hfi_thresholds", mock_hfi_thresholds)
@patch("app.routers.fba.get_all_sfms_fuel_types", mock_sfms_fuel_types)
@patch("app.routers.fba.get_zone_ids_in_centre", mock_zone_ids_in_centre)
@pytest.mark.usefixtures("mock_jwt_decode")
def test_get_fire_center_info_authorized(client: TestClient):
    """Allowed to get fire centre info when authorized"""
    response = client.get(get_fire_centre_info_url)
    assert response.status_code == 200
    assert response.json()["Kamloops Fire Centre"]["1"][0]["fuel_type"]["fuel_type_id"] == 1
    assert response.json()["Kamloops Fire Centre"]["1"][0]["threshold"]["id"] == 1
    assert response.json()["Kamloops Fire Centre"]["1"][0]["critical_hours"]["start_time"] == 9.0
    assert response.json()["Kamloops Fire Centre"]["1"][0]["critical_hours"]["end_time"] == 11.0
    assert math.isclose(response.json()["Kamloops Fire Centre"]["1"][0]["fuel_area"], 0.01)
    assert math.isclose(response.json()["Kamloops Fire Centre"]["1"][0]["area"], 0.005)


@patch("app.routers.fba.get_auth_header", mock_get_auth_header)
@patch("app.routers.fba.get_run_datetimes", mock_get_sfms_run_datetimes)
@pytest.mark.usefixtures("mock_jwt_decode")
def test_get_sfms_run_datetimes_authorized(client: TestClient):
    """Allowed to get sfms run datetimes when authorized"""
    response = client.get(get_sfms_run_datetimes_url)
    assert response.status_code == 200
    assert response.json()[0] == datetime(year=2024, month=1, day=1, hour=1, tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@patch("app.routers.fba.get_auth_header", mock_get_auth_header)
@patch("app.routers.fba.get_zonal_tpi_stats", mock_get_tpi_stats)
@patch("app.routers.fba.get_fire_zone_tpi_fuel_areas", mock_get_fire_zone_tpi_fuel_areas)
@pytest.mark.usefixtures("mock_jwt_decode")
def test_get_fire_zone_tpi_stats_authorized(client: TestClient):
    """Allowed to get fire zone tpi stats when authorized"""
    response = client.get(get_fire_zone_tpi_stats_url)
    square_metres = math.pow(mock_tpi_stats.pixel_size_metres, 2)
    assert response.status_code == 200
    assert response.json()["fire_zone_id"] == 1
    assert response.json()["valley_bottom_hfi"] == mock_tpi_stats.valley_bottom * square_metres
    assert response.json()["mid_slope_hfi"] == mock_tpi_stats.mid_slope * square_metres
    assert response.json()["upper_slope_hfi"] == mock_tpi_stats.upper_slope * square_metres
    assert response.json()["valley_bottom_tpi"] == mock_tpi_fuel_area_1.fuel_area
    assert response.json()["mid_slope_tpi"] == mock_tpi_fuel_area_2.fuel_area
    assert response.json()["upper_slope_tpi"] == mock_tpi_fuel_area_3.fuel_area


@patch("app.routers.fba.get_auth_header", mock_get_auth_header)
@patch("app.routers.fba.get_zonal_tpi_stats", mock_get_tpi_stats_none)
@patch("app.routers.fba.get_fire_zone_tpi_fuel_areas", mock_get_fire_zone_tpi_fuel_areas_none)
@pytest.mark.usefixtures("mock_jwt_decode")
def test_get_fire_zone_tpi_stats_authorized_none(client: TestClient):
    """Returns none for TPI stats when there are no stats available"""
    response = client.get(get_fire_zone_tpi_stats_url)
    assert response.status_code == 200
    assert response.json()["fire_zone_id"] == 1
    assert response.json()["valley_bottom_hfi"] is None
    assert response.json()["mid_slope_hfi"] is None
    assert response.json()["upper_slope_hfi"] is None
    assert response.json()["valley_bottom_tpi"] is None
    assert response.json()["mid_slope_tpi"] is None
    assert response.json()["upper_slope_tpi"] is None


@patch("app.routers.fba.get_auth_header", mock_get_auth_header)
@patch("app.routers.fba.get_centre_tpi_stats", mock_get_centre_tpi_stats)
@patch("app.routers.fba.get_fire_centre_tpi_fuel_areas", mock_get_fire_centre_tpi_fuel_areas)
@pytest.mark.usefixtures("mock_jwt_decode")
def test_get_fire_centre_tpi_stats_authorized(client: TestClient):
    """Allowed to get fire zone tpi stats when authorized"""
    response = client.get(get_fire_centre_tpi_stats_url)
    square_metres = math.pow(mock_centre_tpi_stats_2.pixel_size_metres, 2)
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["fire_centre_name"] == mock_fire_centre_name
    assert json_response["firezone_tpi_stats"][0]["fire_zone_id"] == 1
    assert json_response["firezone_tpi_stats"][0]["valley_bottom_hfi"] == mock_centre_tpi_stats_1.valley_bottom * square_metres
    assert json_response["firezone_tpi_stats"][0]["mid_slope_hfi"] == mock_centre_tpi_stats_1.mid_slope * square_metres
    assert json_response["firezone_tpi_stats"][0]["upper_slope_hfi"] == mock_centre_tpi_stats_1.upper_slope * square_metres
    assert json_response["firezone_tpi_stats"][0]["valley_bottom_tpi"] == mock_centre_tpi_fuel_area_1.fuel_area
    assert json_response["firezone_tpi_stats"][0]["mid_slope_tpi"] == mock_centre_tpi_fuel_area_2.fuel_area
    assert json_response["firezone_tpi_stats"][0]["upper_slope_tpi"] == mock_centre_tpi_fuel_area_3.fuel_area

    assert json_response["firezone_tpi_stats"][1]["fire_zone_id"] == 2
    assert json_response["firezone_tpi_stats"][1]["valley_bottom_hfi"] == mock_centre_tpi_stats_2.valley_bottom * square_metres
    assert json_response["firezone_tpi_stats"][1]["mid_slope_hfi"] == mock_centre_tpi_stats_2.mid_slope * square_metres
    assert json_response["firezone_tpi_stats"][1]["upper_slope_hfi"] == mock_centre_tpi_stats_2.upper_slope * square_metres
    assert json_response["firezone_tpi_stats"][1]["valley_bottom_tpi"] is None
    assert json_response["firezone_tpi_stats"][1]["mid_slope_tpi"] is None
    assert json_response["firezone_tpi_stats"][1]["upper_slope_tpi"] is None
