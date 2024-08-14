from unittest.mock import patch
import math
import pytest
from fastapi.testclient import TestClient
from datetime import date, datetime, timezone
from app.db.models.auto_spatial_advisory import AdvisoryElevationStats, AdvisoryTPIStats, RunParameters

get_fire_centres_url = "/api/fba/fire-centers"
get_fire_zone_areas_url = "/api/fba/fire-shape-areas/forecast/2022-09-27/2022-09-27"
get_fire_zone_tpi_stats_url = "/api/fba/fire-zone-tpi-stats/forecast/2022-09-27/2022-09-27/1"
get_fire_zone_elevation_info_url = "/api/fba/fire-zone-elevation-info/forecast/2022-09-27/2022-09-27/1"
get_sfms_run_datetimes_url = "/api/fba/sfms-run-datetimes/forecast/2022-09-27"


decode_fn = "jwt.decode"
mock_tpi_stats = AdvisoryTPIStats(id=1, advisory_shape_id=1, valley_bottom=1, mid_slope=2, upper_slope=3, pixel_size_metres=50)
mock_elevation_info = [AdvisoryElevationStats(id=1, advisory_shape_id=1, threshold=1, minimum=1.0, quartile_25=2.0, median=3.0, quartile_75=4.0, maximum=5.0)]
mock_sfms_run_datetimes = [
    RunParameters(id=1, run_type="forecast", run_datetime=datetime(year=2024, month=1, day=1, hour=1, tzinfo=timezone.utc), for_date=date(year=2024, month=1, day=2))
]


async def mock_get_fire_centres(*_, **__):
    return []


async def mock_get_hfi_area(*_, **__):
    return []


async def mock_get_auth_header(*_, **__):
    return {}


async def mock_get_tpi_stats(*_, **__):
    return mock_tpi_stats


async def mock_get_elevation_info(*_, **__):
    return mock_elevation_info


async def mock_get_sfms_run_datetimes(*_, **__):
    return mock_sfms_run_datetimes


@pytest.fixture()
def client():
    from app.main import app as test_app

    with TestClient(test_app) as test_client:
        yield test_client


@pytest.mark.parametrize(
    "endpoint",
    [get_fire_centres_url, get_fire_zone_areas_url, get_fire_zone_tpi_stats_url, get_fire_zone_elevation_info_url, get_sfms_run_datetimes_url],
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


@patch("app.routers.fba.get_auth_header", mock_get_auth_header)
@patch("app.routers.fba.get_zonal_elevation_stats", mock_get_elevation_info)
@pytest.mark.usefixtures("mock_jwt_decode")
def test_get_fire_zone_elevation_info_authorized(client: TestClient):
    """Allowed to get fire zone elevation info when authorized"""
    response = client.get(get_fire_zone_elevation_info_url)
    assert response.status_code == 200
    assert response.json()["hfi_elevation_info"][0]["threshold"] == mock_elevation_info[0].threshold
    assert response.json()["hfi_elevation_info"][0]["elevation_info"]["minimum"] == mock_elevation_info[0].minimum
    assert response.json()["hfi_elevation_info"][0]["elevation_info"]["quartile_25"] == mock_elevation_info[0].quartile_25
    assert response.json()["hfi_elevation_info"][0]["elevation_info"]["median"] == mock_elevation_info[0].median
    assert response.json()["hfi_elevation_info"][0]["elevation_info"]["quartile_75"] == mock_elevation_info[0].quartile_75
    assert response.json()["hfi_elevation_info"][0]["elevation_info"]["maximum"] == mock_elevation_info[0].maximum


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
@pytest.mark.usefixtures("mock_jwt_decode")
def test_get_fire_zone_tpi_stats_authorized(client: TestClient):
    """Allowed to get fire zone tpi stats when authorized"""
    response = client.get(get_fire_zone_tpi_stats_url)
    square_metres = math.pow(mock_tpi_stats.pixel_size_metres, 2)
    assert response.status_code == 200
    assert response.json()["stats"][0]["fire_zone_id"] == 1
    assert response.json()["stats"][0]["valley_bottom"] == mock_tpi_stats.valley_bottom * square_metres
    assert response.json()["stats"][0]["mid_slope"] == mock_tpi_stats.mid_slope * square_metres
    assert response.json()["stats"][0]["upper_slope"] == mock_tpi_stats.upper_slope * square_metres
