from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from wps_shared.schemas.stations import WeatherStationGroupMembersResponse
from wps_wf1.parsers import unique_weather_stations_mapper
from wps_wf1.wfwx_api import WfwxApi


def member(station_id="station-1", code=1, **fields):
    return {
        "station": {
            "id": station_id,
            "stationCode": code,
            "displayLabel": f"Station {code}",
            "stationStatus": {"id": "ACTIVE"},
            "zone": None,
            "fireCentre": {"id": 1, "displayLabel": "Centre"},
            **fields,
        }
    }


def api_for(groups):
    api = WfwxApi.__new__(WfwxApi)
    api._get_auth_header = AsyncMock(return_value={})
    api.wfwx_client = SimpleNamespace(
        fetch_stations_by_group_id=AsyncMock(side_effect=lambda _, group_id: groups[group_id])
    )
    api.get_station_data = AsyncMock()
    return api


@pytest.mark.parametrize("height", [625, 0, -5, None])
def test_group_mapper_preserves_nullable_elevation(height):
    result = unique_weather_stations_mapper([member(elevation=height)])
    response = WeatherStationGroupMembersResponse(stations=result).model_dump(mode="json")
    assert response["stations"][0]["elevation"] == height


@pytest.mark.anyio
async def test_group_responses_supply_elevations_without_another_request():
    api = api_for(
        {
            "a": [member(elevation=625), member("station-2", 2, elevation=0)],
            "b": [
                member("station-3", 3, elevation=-5),
                member("station-4", 4, elevation=None),
                member("station-5", 5),
            ],
        }
    )
    stations = await api.get_stations_by_group_ids(["a", "b"])
    assert [station.elevation for station in stations] == [625, 0, -5, None, None]
    assert [station.station_code for station in stations] == [1, 2, 3, 4, 5]
    api.get_station_data.assert_not_called()
    assert api.wfwx_client.fetch_stations_by_group_id.await_count == 2


@pytest.mark.anyio
@pytest.mark.parametrize("group_ids", [[], ["empty"]])
async def test_empty_groups_do_not_fetch_supplementary_metadata(group_ids):
    api = api_for({"empty": []})
    assert await api.get_stations_by_group_ids(group_ids) == []
    api.get_station_data.assert_not_called()
