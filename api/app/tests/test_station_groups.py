from httpx import AsyncClient
import pytest
from unittest.mock import patch


station_groups_get_url = '/api/stations/groups'
station_groups_members_post_url = '/api/stations/groups/members'


@pytest.fixture()
async def async_client():
    from app.main import app as test_app

    async with AsyncClient(app=test_app, base_url="http://test") as test_client:
        yield test_client


@pytest.mark.anyio
async def test_root(anyio_backend, async_client: AsyncClient):
    response = await async_client.get(station_groups_get_url)
    assert response.status_code == 401


@pytest.mark.anyio
async def test_get_station_groups_unauthorized(anyio_backend, async_client: AsyncClient):
    """ unauthenticated clients have no access """
    response = await async_client.get(station_groups_get_url)
    assert response.status_code == 401


@patch('app.wildfire_one.wfwx_api.get_station_groups', return_value=[])
@pytest.mark.usefixtures("mock_jwt_decode")
@pytest.mark.anyio
async def test_get_station_groups_authorized(anyio_backend, async_client: AsyncClient):
    """ authenticated client can access """
    response = await async_client.get(station_groups_get_url)
    assert response.status_code == 200


@pytest.mark.anyio
async def test_get_station_groups_members_unauthorized(anyio_backend, async_client: AsyncClient):
    """ unauthenticated clients have no access """
    response = await async_client.post(station_groups_members_post_url)
    assert response.status_code == 401


@patch('app.wildfire_one.wfwx_api.get_stations_by_group_ids', return_value=[])
@pytest.mark.usefixtures("mock_jwt_decode")
@pytest.mark.anyio
async def test_get_station_groups_members_authorized(anyio_backend, async_client: AsyncClient):
    """ unauthenticated clients have no access """
    response = await async_client.post(station_groups_members_post_url, json={"group_ids": ["1"]})
    assert response.status_code == 200
