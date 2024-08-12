from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

from app.db.models.auto_spatial_advisory import AdvisoryTPIStats

get_fire_centres_url = "/api/fba/fire-centers"
get_fire_zone_areas_url = "/api/fba/fire-shape-areas/forecast/2022-09-27/2022-09-27"
get_fire_zone_tpi_stats_url = "/api/fba/fire-zone-tpi-stats/forecast/2022-09-27/2022-09-27/1"
decode_fn = "jwt.decode"
mock_tpi_stats = AdvisoryTPIStats(id=1, advisory_shape_id=1, valley_bottom=1, mid_slope=2, upper_slope=3, pixel_size_metres=50)


async def mock_get_fire_centres(*_, **__):
    return []


async def mock_get_hfi_area(*_, **__):
    return []


async def mock_get_auth_header(*_, **__):
    return {}


async def mock_get_tpi_stats(*_, **__):
    return mock_tpi_stats


@pytest.fixture()
def client():
    from app.main import app as test_app

    with TestClient(test_app) as test_client:
        yield test_client


@patch("app.routers.fba.get_auth_header", mock_get_auth_header)
@patch("app.routers.fba.get_fire_centers", mock_get_fire_centres)
@pytest.mark.usefixtures("mock_jwt_decode")
def test_get_fire_centres_authorized(client: TestClient):
    """Allowed to get fire centres when authorized"""
    response = client.get(get_fire_centres_url)
    assert response.status_code == 200


def test_get_fire_centres_unauthorized(client: TestClient):
    """Forbidden to get fire centres when unauthorized"""

    response = client.get(get_fire_centres_url)
    assert response.status_code == 401


def test_get_fire_zone_areas_unauthorized(client: TestClient):
    """Forbidden to get fire zone areas when unauthorized"""

    response = client.get(get_fire_zone_areas_url)
    assert response.status_code == 401


@patch("app.routers.fba.get_auth_header", mock_get_auth_header)
@patch("app.routers.fba.get_zonal_tpi_stats", mock_get_tpi_stats)
@pytest.mark.usefixtures("mock_jwt_decode")
def test_get_fire_zone_tpi_stats_authorized(client: TestClient):
    """Allowed to get fire zone tpi stats when authorized"""
    response = client.get(get_fire_zone_tpi_stats_url)
    assert response.status_code == 200
    assert response.json()["fire_zone_id"] == 1
    assert response.json()["valley_bottom"] == mock_tpi_stats.valley_bottom * mock_tpi_stats.pixel_size_metres
    assert response.json()["mid_slope"] == mock_tpi_stats.mid_slope * mock_tpi_stats.pixel_size_metres
    assert response.json()["upper_slope"] == mock_tpi_stats.upper_slope * mock_tpi_stats.pixel_size_metres


def test_get_fire_zone_tpi_stats_unauthorized(client: TestClient):
    """Forbidden to get fire zone tpi stats when unauthorized"""

    response = client.get(get_fire_zone_tpi_stats_url)
    assert response.status_code == 401
