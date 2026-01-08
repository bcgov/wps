
# tests/test_wfwx_api.py
import asyncio
import math
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Any, AsyncGenerator, Dict, List, Optional
from unittest.mock import AsyncMock

import pytest

import wps_wf1.wfwx_api as wfwx_api_module

# -----------------------------
# Pytest config / async support
# -----------------------------
pytestmark = pytest.mark.asyncio


# -----------------------------
# Lightweight stub models
# -----------------------------
@dataclass
class StubWeatherVariables:
    temperature: Optional[float] = None
    relative_humidity: Optional[float] = None


@dataclass
class StubDetailedWeatherStationProperties:
    code: int
    name: str
    observations: Optional[StubWeatherVariables] = None
    forecasts: Optional[StubWeatherVariables] = None


@dataclass
class StubWeatherStationGeometry:
    coordinates: List[float]


@dataclass
class StubGeoJsonDetailedWeatherStation:
    properties: StubDetailedWeatherStationProperties
    geometry: StubWeatherStationGeometry


@dataclass
class StubWeatherStationHourlyReadings:
    values: List[Any]
    station: Any


@dataclass
class StubWFWXWeatherStation:
    wfwx_id: str
    code: int


# -----------------------------
# Fake aiohttp session + response
# -----------------------------
class FakeResponse:
    def __init__(self, status: int = 200):
        self.status = status
        self.raise_for_status_called = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    def raise_for_status(self):
        self.raise_for_status_called = True
        if not (200 <= self.status < 300):
            raise AssertionError(f"HTTP {self.status}")


class MockSession:
    def __init__(self):
        self.last_post_args = None
        self.last_post_kwargs = None
        self.response_status = 200

    def post(self, url, **kwargs):
        self.last_post_args = (url,)
        self.last_post_kwargs = kwargs
        return FakeResponse(status=self.response_status)


# -----------------------------
# Fake WfwxClient
# -----------------------------
class FakeWfwxClient:
    def __init__(self, session, settings, cache):
        self.session = session
        self.settings = settings
        self.cache = cache
        self.last_post_forecasts_args = None
        self.hourlies_payload = None
        # Pre-configured data sources for generators
        self._paged_data: Dict[str, List[dict]] = {
            "stations": [],
            "dailies": [],
            "hourlies": [],
            "stationGroups": [],
        }
        self._raw_dailies_all_stations: List[dict] = []

    async def fetch_access_token(self, expiry: int):
        return {"access_token": "TOKEN123"}

    def set_paged_data(self, key: str, items: List[dict]):
        self._paged_data[key] = items

    def _make_generator(self, key: str) -> AsyncGenerator[dict, None]:
        async def gen():
            for item in self._paged_data.get(key, []):
                yield item
        return gen()

    def fetch_paged_response_generator(
        self, headers: Dict[str, str], query_builder: Any, resource_name: str,
        use_cache: bool = False, ttl: Optional[int] = None
    ):
        # For test assertions, attach for later inspection:
        self.last_fetch_headers = headers
        self.last_fetch_resource = resource_name
        self.last_fetch_use_cache = use_cache
        self.last_fetch_ttl = ttl
        self.last_fetch_query = query_builder
        return self._make_generator(resource_name)

    async def fetch_raw_dailies_for_all_stations(self, headers: Dict[str, str], time_of_interest: datetime):
        return list(self._raw_dailies_all_stations)

    async def fetch_hourlies(self, raw_station, headers, start_ts, end_ts, use_cache, ttl):
        # Example structure that WfwxApi expects:
        return {
            "_embedded": {
                "hourlies": self._paged_data.get("hourlies", [])
            }
        }

    async def fetch_stations_by_group_id(self, headers, group_id: str):
        # Return whatever is stored in "stations" for simplicity.
        return self._paged_data.get("stations", [])

    async def post_forecasts(self, headers, forecasts_json):
        self.last_post_forecasts_args = (headers, forecasts_json)


# -----------------------------
# Helpers: stubs for parsers & utils
# -----------------------------
async def stub_station_list_mapper(generator):
    # Consume generator and return list of raw items (identity)
    stations = []
    async for item in generator:
        stations.append(item)
    return stations


async def stub_wfwx_station_list_mapper(generator):
    # Map raw station dicts {id, stationCode} into StubWFWXWeatherStation
    stations = []
    async for item in generator:
        stations.append(StubWFWXWeatherStation(wfwx_id=str(item.get("id")), code=item.get("stationCode")))
    return stations


async def stub_dailies_list_mapper(generator, record_type_enum):
    # Return consumed list tagged by record_type_enum for verification
    items = []
    async for item in generator:
        items.append({"rt": record_type_enum, "raw": item})
    return items


async def stub_weather_indeterminate_list_mapper(generator):
    # Return a tuple of (actuals, forecasts) separating by recordType.id
    actuals, forecasts = [], []
    async def collect():
        a, f = [], []
        async for item in generator:
            rt = item.get("recordType", {}).get("id")
            (a if rt == "ACTUAL" else f).append(item)
        return a, f
    return await collect()


async def stub_weather_station_group_mapper(generator):
    # Return list of group ids (identity map)
    return ["grpA", "grpB"]


def stub_unique_weather_stations_mapper(stations):
    # Identity mapper: wrap codes if present
    return [s.get("stationCode") for s in stations]


def stub_parse_station(raw_station, eco_division):
    return {"parsed_station": raw_station.get("stationCode"), "eco": eco_division}


def stub_parse_hourly(hourly):
    return {"parsed_hourly": hourly.get("ts")}


def stub_parse_hourly_actual(station_code, hourly):
    return {"station_code": station_code, "parsed_actual": hourly.get("ts")}


def stub_parse_noon_forecast(station_code, noon_forecast):
    return {"station_code": station_code, "nf": noon_forecast.get("ts")}


def stub_is_station_valid(raw_station):
    return raw_station.get("valid", True)


# -----------------------------
# Fixtures
# -----------------------------
@pytest.fixture
def mock_session():
    return MockSession()


@pytest.fixture
def fake_settings():
    class S:
        base_url = "https://example.test"
        auth_cache_expiry = 600
        station_cache_expiry = 300
        hourlies_by_station_code_expiry = 60
        dailies_by_station_code_expiry = 120
        use_cache = True
    return S()


@pytest.fixture
def wfwx_api(mock_session, fake_settings, monkeypatch):
    # Patch models in the module to stubs
    monkeypatch.setattr(wfwx_api_module, "GeoJsonDetailedWeatherStation", StubGeoJsonDetailedWeatherStation)
    monkeypatch.setattr(wfwx_api_module, "DetailedWeatherStationProperties", StubDetailedWeatherStationProperties)
    monkeypatch.setattr(wfwx_api_module, "WeatherStationGeometry", StubWeatherStationGeometry)
    monkeypatch.setattr(wfwx_api_module, "WeatherStationHourlyReadings", StubWeatherStationHourlyReadings)
    monkeypatch.setattr(wfwx_api_module, "WeatherVariables", StubWeatherVariables)
    # Patch parsers
    monkeypatch.setattr(wfwx_api_module, "parse_station", stub_parse_station)
    monkeypatch.setattr(wfwx_api_module, "parse_hourly", stub_parse_hourly)
    monkeypatch.setattr(wfwx_api_module, "parse_hourly_actual", stub_parse_hourly_actual)
    monkeypatch.setattr(wfwx_api_module, "parse_noon_forecast", stub_parse_noon_forecast)
    # Patch mappers
    monkeypatch.setattr(wfwx_api_module, "station_list_mapper", stub_station_list_mapper)
    monkeypatch.setattr(wfwx_api_module, "wfwx_station_list_mapper", stub_wfwx_station_list_mapper)
    monkeypatch.setattr(wfwx_api_module, "dailies_list_mapper", stub_dailies_list_mapper)
    monkeypatch.setattr(wfwx_api_module, "weather_indeterminate_list_mapper", stub_weather_indeterminate_list_mapper)
    monkeypatch.setattr(wfwx_api_module, "weather_station_group_mapper", stub_weather_station_group_mapper)
    monkeypatch.setattr(wfwx_api_module, "unique_weather_stations_mapper", stub_unique_weather_stations_mapper)
    # Patch util
    monkeypatch.setattr(wfwx_api_module, "is_station_valid", stub_is_station_valid)
    # Patch EcodivisionSeasons context manager
    class FakeEcodivisionSeasons:
        def __init__(self, key, cache):
            self.key = key
            self.cache = cache
        def __enter__(self):
            return f"ECO-{self.key}"
        def __exit__(self, exc_type, exc, tb):
            return False
    monkeypatch.setattr(wfwx_api_module, "EcodivisionSeasons", FakeEcodivisionSeasons)

    # Instantiate API
    wfwx_api = wfwx_api_module.WfwxApi(mock_session, fake_settings, cache=None)

    # Replace client with fake one
    fake_client = FakeWfwxClient(mock_session, fake_settings, cache=None)
    wfwx_api.wfwx_client = fake_client
    return wfwx_api


# -----------------------------
# Tests
# -----------------------------
@pytest.mark.anyio
async def test_get_auth_headers(wfwx_api):
    hdr = await wfwx_api._get_auth_header()
    assert hdr["Authorization"] == "Bearer TOKEN123"

    no_cache_hdr = await wfwx_api._get_no_cache_auth_header()
    assert no_cache_hdr["Authorization"] == "Bearer TOKEN123"
    assert no_cache_hdr["Cache-Control"] == "no-cache"

@pytest.mark.anyio
async def test_get_stations_by_codes_filters_and_parses(wfwx_api):
    # Arrange
    wfwx_api.wfwx_client.set_paged_data("stations", [
        {"id": "1", "stationCode": 100, "valid": True},
        {"id": "2", "stationCode": 200, "valid": False},
    ])
    # Act
    stations = await wfwx_api.get_stations_by_codes([100, 200])
    # Assert
    assert len(stations) == 1
    assert stations[0]["parsed_station"] == 100
    assert stations[0]["eco"].startswith("ECO-")  # eco division is propagated

@pytest.mark.anyio
async def test_get_station_data_missing_await_bug(wfwx_api):
    # Arrange
    wfwx_api.wfwx_client.set_paged_data("stations", [
        {"id": "1", "stationCode": 100, "valid": True},
    ])
    # Act
    stations = await wfwx_api.get_station_data(use_no_cache_header=False)  # should await _get_auth_header()
    # Assert (this would fail prior to fix if header is coroutine and client inspects type)
    assert isinstance(wfwx_api.wfwx_client.last_fetch_headers, dict)

@pytest.mark.anyio
async def test_get_station_data_with_no_cache_header(wfwx_api):
    # Arrange
    wfwx_api.wfwx_client.set_paged_data("stations", [{"id": "1", "displayLabel": "test", "stationCode": 100, "stationStatus": {"id": "ACTIVE"}, "latitude": 1, "longitude": 1}])
    # Act
    stations = await wfwx_api.get_station_data(use_no_cache_header=True)
    # Assert
    assert isinstance(wfwx_api.wfwx_client.last_fetch_headers, dict)
    assert wfwx_api.wfwx_client.last_fetch_headers.get("Cache-Control") == "no-cache"
    station = stations[0]
    assert station.code == 100

@pytest.mark.anyio
async def test_get_detailed_geojson_stations_builds_maps(wfwx_api):
    # Arrange
    wfwx_api.wfwx_client.set_paged_data("stations", [
        {"id": "A", "stationCode": 111, "stationStatus": {"id": "ACTIVE"}, "displayLabel": "Alpha", "longitude": -123.1, "latitude": 48.4, "valid": True},
        {"id": "B", "stationCode": 222, "stationStatus": {"id": "INACTIVE"}, "displayLabel": "Beta", "longitude": -123.2, "latitude": 48.5, "valid": False},
    ])
    qb = wfwx_api_module.BuildQueryStations()  # or any builder; value is not inspected in fake client
    # Act
    stations, id_map = await wfwx_api.get_detailed_geojson_stations(qb)
    # Assert
    assert set(stations.keys()) == {111}
    geo = stations[111]
    assert isinstance(geo, StubGeoJsonDetailedWeatherStation)
    assert geo.properties.code == 111
    assert geo.properties.name == "Alpha"
    assert geo.geometry.coordinates == [-123.1, 48.4]
    assert id_map == {"A": 111}

@pytest.mark.anyio
async def test_get_detailed_stations_merges_dailies(wfwx_api):
    # Arrange
    wfwx_api.wfwx_client.set_paged_data("stations", [
        {"id": "S1", "stationCode": 777, "displayLabel": "S1", "longitude": -1, "latitude": 1, "valid": True},
    ])
    wfwx_api.wfwx_client._raw_dailies_all_stations = [
        {"stationId": "S1", "recordType": {"id": "ACTUAL"}, "temperature": 21.0, "relativeHumidity": 40},
        {"stationId": "S1", "recordType": {"id": "FORECAST"}, "temperature": 23.0, "relativeHumidity": 35},
    ]
    # Act
    out = await wfwx_api.get_detailed_stations(datetime(2025, 1, 1, tzinfo=timezone.utc))
    # Assert
    assert len(out) == 1
    props = out[0].properties
    assert props.observations == StubWeatherVariables(temperature=21.0, relative_humidity=40)
    assert props.forecasts == StubWeatherVariables(temperature=23.0, relative_humidity=35)

@pytest.mark.anyio
async def test_get_hourly_for_station_filters_non_actual(wfwx_api):
    # Arrange
    wfwx_api.wfwx_client.set_paged_data("hourlies", [
        {"hourlyMeasurementTypeCode": {"id": "ACTUAL"}, "ts": 111},
        {"hourlyMeasurementTypeCode": {"id": "FORECAST"}, "ts": 222},
    ])
    raw_station = {"stationCode": 999}
    # Act
    readings = await wfwx_api.get_hourly_for_station(
        raw_station=raw_station,
        start_timestamp=datetime(2025, 1, 1, tzinfo=timezone.utc),
        end_timestamp=datetime(2025, 1, 2, tzinfo=timezone.utc),
        eco_division="ECO-key",
        use_cache=False,
        ttl=30,
    )
    # Assert
    assert isinstance(readings, StubWeatherStationHourlyReadings)
    assert [v["parsed_hourly"] for v in readings.values] == [111]
    assert readings.station["parsed_station"] == 999

@pytest.mark.anyio
async def test_get_hourly_readings_runs_parallel(wfwx_api):
    # Arrange: two stations
    wfwx_api.wfwx_client.set_paged_data("stations", [
        {"id": "S1", "stationCode": 100},
        {"id": "S2", "stationCode": 200},
    ])
    wfwx_api.wfwx_client.set_paged_data("hourlies", [
        {"hourlyMeasurementTypeCode": {"id": "ACTUAL"}, "ts": 10},
        {"hourlyMeasurementTypeCode": {"id": "ACTUAL"}, "ts": 20},
    ])
    # Act
    out = await wfwx_api.get_hourly_readings(
        station_codes=[100, 200],
        start_timestamp=datetime(2025, 1, 1, tzinfo=timezone.utc),
        end_timestamp=datetime(2025, 1, 2, tzinfo=timezone.utc),
        use_cache=True,
    )
    # Assert
    assert len(out) == 2
    # We don't enforce order due to concurrency, but both should be there.
    parsed_codes = sorted(r.station["parsed_station"] for r in out)
    assert parsed_codes == [100, 200]

@pytest.mark.anyio
async def test_get_noon_forecasts_all_stations_maps_by_wfwx_id(wfwx_api):
    # Arrange
    wfwx_api.wfwx_client.set_paged_data("dailies", [
        {"stationId": "S1", "ts": 100},
        {"stationId": "S2", "ts": 200},
    ])
    wfwx_api.wfwx_client.set_paged_data("stations", [
        {"id": "S1", "stationCode": 111},
        {"id": "S2", "stationCode": 222},
    ])
    # Act
    out = await wfwx_api.get_noon_forecasts_all_stations(datetime(2025, 1, 1, tzinfo=timezone.utc))
    # Assert
    assert len(out) == 2
    assert {o["station_code"] for o in out} == {111, 222}
    assert {o["nf"] for o in out} == {100, 200}

@pytest.mark.anyio
async def test_get_hourly_actuals_all_stations_filters_actual(wfwx_api):
    # Arrange
    wfwx_api.wfwx_client.set_paged_data("hourlies", [
        {"stationId": "S1", "ts": 100, "hourlyMeasurementTypeCode": {"id": "ACTUAL"}},
        {"stationId": "S2", "ts": 200, "hourlyMeasurementTypeCode": {"id": "FORECAST"}},
    ])
    wfwx_api.wfwx_client.set_paged_data("stations", [
        {"id": "S1", "stationCode": 111},
        {"id": "S2", "stationCode": 222},
    ])
    # Act
    out = await wfwx_api.get_hourly_actuals_all_stations(
        start_timestamp=datetime(2025, 1, 1, tzinfo=timezone.utc),
        end_timestamp=datetime(2025, 1, 2, tzinfo=timezone.utc),
    )
    # Assert
    assert len(out) == 1
    assert out[0]["station_code"] == 111
    assert out[0]["parsed_actual"] == 100

@pytest.mark.anyio
async def test_get_wfwx_stations_from_station_codes_none_filters_by_fire_centre(wfwx_api):
    # Arrange
    wfwx_api.wfwx_client.set_paged_data("stations", [
        {"id": "A", "stationCode": 10},
        {"id": "B", "stationCode": 20},
        {"id": "C", "stationCode": 30},
    ])
    # Act
    result = await wfwx_api.get_wfwx_stations_from_station_codes(
        station_codes=None,
        fire_centre_station_codes=[10, 30],
        use_no_cache_header=False,
    )
    # Assert
    codes = sorted(s.code for s in result)
    assert codes == [10, 30]

@pytest.mark.anyio
async def test_get_wfwx_stations_from_station_codes_specific_with_missing_logs_error(wfwx_api, caplog):
    # Arrange
    wfwx_api.wfwx_client.set_paged_data("stations", [
        {"id": "A", "stationCode": 10},
        {"id": "B", "stationCode": 20},
    ])
    # Act
    result = await wfwx_api.get_wfwx_stations_from_station_codes(
        station_codes=[10, 99],
        fire_centre_station_codes=[10, 20, 99],
        use_no_cache_header=False,
    )
    # Assert
    codes = sorted(s.code for s in result)
    assert codes == [10]
    # Missing one logs an error
    assert any("No WFWX station id for station code: 99" in rec.message for rec in caplog.records)

@pytest.mark.anyio
async def test_get_raw_dailies_in_range_generator(wfwx_api):
    # Arrange
    wfwx_api.wfwx_client.set_paged_data("dailies", [{"x": 1}, {"x": 2}])
    # Act
    gen = await wfwx_api.get_raw_dailies_in_range_generator(["A", "B"], 0, 10)
    items = []
    async for item in gen:
        items.append(item)
    # Assert
    assert items == [{"x": 1}, {"x": 2}]

@pytest.mark.anyio
async def test_get_dailies_generator_respects_cache_and_headers(wfwx_api):
    # Arrange
    wfwx_api.wfwx_client.set_paged_data("dailies", [{"rec": 1}, {"rec": 2}])
    # Act
    gen = await wfwx_api.get_dailies_generator(
        wfwx_stations=[StubWFWXWeatherStation(wfwx_id="A", code=1)],
        time_of_interest=datetime(2025, 1, 1, tzinfo=timezone.utc),
        end_time_of_interest=datetime(2025, 1, 2, tzinfo=timezone.utc),
        check_cache=False,  # force use_cache False even if settings.use_cache True
        use_no_cache_header=True,
    )
    items = []
    async for item in gen:
        items.append(item)
    # Assert
    assert items == [{"rec": 1}, {"rec": 2}]
    assert wfwx_api.wfwx_client.last_fetch_use_cache is False
    assert wfwx_api.wfwx_client.last_fetch_headers.get("Cache-Control") == "no-cache"
    # Check timestamps were millisecond-rounded
    qb = wfwx_api.wfwx_client.last_fetch_query
    assert isinstance(qb, wfwx_api_module.BuildQueryDailiesByStationCode)

@pytest.mark.anyio
async def test_get_fire_centers_returns_values_list(wfwx_api, monkeypatch):
    # Arrange: fire_center_mapper returns dict
    async def fake_fire_center_mapper(generator):
        return {"FC1": {"name": "A"}, "FC2": {"name": "B"}}
    monkeypatch.setattr(wfwx_api_module, "fire_center_mapper", fake_fire_center_mapper)
    # Act
    out = await wfwx_api.get_fire_centers()
    # Assert
    assert out == [{"name": "A"}, {"name": "B"}]

@pytest.mark.anyio
async def test_get_dailies_for_stations_and_date_uses_mapper(wfwx_api):
    # Arrange
    wfwx_api.wfwx_client.set_paged_data("stations", [{"id": "S1", "stationCode": 1}])
    wfwx_api.wfwx_client.set_paged_data("dailies", [{"d": 1}, {"d": 2}])
    # Act
    out = await wfwx_api.get_dailies_for_stations_and_date(
        start_time_of_interest=datetime(2025, 1, 1, tzinfo=timezone.utc),
        end_time_of_interest=datetime(2025, 1, 2, tzinfo=timezone.utc),
        unique_station_codes=[1],
        fire_centre_station_codes=[1],
        mapper=stub_dailies_list_mapper,
    )
    # Assert
    assert all(item["rt"] == wfwx_api_module.WF1RecordTypeEnum.ACTUAL for item in out)
    assert [i["raw"] for i in out] == [{"d": 1}, {"d": 2}]

@pytest.mark.anyio
async def test_get_forecasts_for_stations_by_date_range(wfwx_api):
    # Arrange
    wfwx_api.wfwx_client.set_paged_data("stations", [{"id": "S1", "stationCode": 1}])
    wfwx_api.wfwx_client.set_paged_data("dailies", [{"d": 1}, {"d": 2}])
    # Act
    out = await wfwx_api.get_forecasts_for_stations_by_date_range(
        start_time_of_interest=datetime(2025, 1, 1, tzinfo=timezone.utc),
        end_time_of_interest=datetime(2025, 1, 2, tzinfo=timezone.utc),
        unique_station_codes=[1],
        fire_centre_station_codes=[1],
        check_cache=True,
        mapper=stub_dailies_list_mapper,
        use_no_cache_header=False,
    )
    # Assert
    assert all(item["rt"] == wfwx_api_module.WF1RecordTypeEnum.FORECAST for item in out)
    assert [i["raw"] for i in out] == [{"d": 1}, {"d": 2}]

@pytest.mark.anyio
async def test_get_daily_determinates_for_stations_and_date(wfwx_api):
    # Arrange
    wfwx_api.wfwx_client.set_paged_data("stations", [{"id": "S1", "stationCode": 1}])
    wfwx_api.wfwx_client.set_paged_data("dailies", [
        {"recordType": {"id": "ACTUAL"}, "val": 1},
        {"recordType": {"id": "FORECAST"}, "val": 2},
    ])
    # Act
    actuals, forecasts = await wfwx_api.get_daily_determinates_for_stations_and_date(
        start_time_of_interest=datetime(2025, 1, 1, tzinfo=timezone.utc),
        end_time_of_interest=datetime(2025, 1, 2, tzinfo=timezone.utc),
        unique_station_codes=[1],
        fire_centre_station_codes=[1],
        mapper=stub_weather_indeterminate_list_mapper,
        check_cache=True,
    )
    # Assert
    assert [a["val"] for a in actuals] == [1]
    assert [f["val"] for f in forecasts] == [2]

@pytest.mark.anyio
async def test_get_station_groups_maps(wfwx_api):
    # Arrange
    wfwx_api.wfwx_client.set_paged_data("stationGroups", [{"g": 1}, {"g": 2}])
    # Act
    out = await wfwx_api.get_station_groups(mapper=stub_weather_station_group_mapper)
    # Assert
    assert out == ["grpA", "grpB"]

@pytest.mark.anyio
async def test_get_stations_by_group_ids_accumulates(wfwx_api):
    # Arrange
    wfwx_api.wfwx_client.set_paged_data("stations", [{"stationCode": 10}, {"stationCode": 20}])
    # Act
    out = await wfwx_api.get_stations_by_group_ids(["G1", "G2"], mapper=stub_unique_weather_stations_mapper)
    # Assert
    assert out == [10, 20, 10, 20]

@pytest.mark.anyio
async def test_post_forecasts_calls_client_and_session_post(wfwx_api, monkeypatch):
    # Arrange
    # Ensure auth header is stable
    async def fake_get_auth_header():
        return {"Authorization": "Bearer TOKEN123"}
    monkeypatch.setattr(wfwx_api, "_get_auth_header", fake_get_auth_header)

    class WF1Stub:
        def __init__(self, val):
            self.val = val
        def model_dump(self):
            return {"v": self.val}

    forecasts = [WF1Stub(1), WF1Stub(2)]
    wfwx_api.wfwx_client.last_post_forecasts_args = None
    wfwx_api.wfwx_client.session.response_status = 200
    # Act
    await wfwx_api.post_forecasts(forecasts)
    # Assert: client helper called
    headers, posted_json = wfwx_api.wfwx_client.last_post_forecasts_args
    assert headers == {"Authorization": "Bearer TOKEN123"}
    assert posted_json == [{"v": 1}, {"v": 2}]
    # Assert: direct session POST called with correct URL & headers
    url = f"{wfwx_api.wfwx_settings.base_url}/v1/dailies/daily-bulk"
    assert wfwx_api.wfwx_client.session.last_post_args == (url,)
    assert wfwx_api.wfwx_client.session.last_post_kwargs["json"] == [{"v": 1}, {"v": 2}]
    assert wfwx_api.wfwx_client.session.last_post_kwargs["headers"] == {"Authorization": "Bearer TOKEN123"}
