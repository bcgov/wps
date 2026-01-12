import types
import pytest

from datetime import datetime


# ---------------------------
# Helpers & Fakes for testing
# ---------------------------
class FakeResponse:
    def __init__(self):
        self.raise_for_status_called = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    def raise_for_status(self):
        self.raise_for_status_called = True


class FakeSession:
    def __init__(self):
        self.last_post = None

    def post(self, url, json=None, headers=None):
        self.last_post = {"url": url, "json": json, "headers": headers}
        return FakeResponse()


# Mock async generator function
async def async_gen(items):
    for item in items:
        yield item


# Mock the underlying wfwx_client
class FakeWfwxClient:
    def __init__(self, session, settings, redis):
        self.session = session
        self.settings = settings
        self.redis = redis
        # Defaults - tests can override these per test via monkeypatch/assignment
        self._access_token = {"access_token": "token123"}

    async def fetch_access_token(self, ttl):
        return self._access_token

    def fetch_paged_response_generator(
        self, headers, query_builder, key, use_cache=False, ttl=None
    ):
        # return an empty generator by default; tests override as needed
        return async_gen([])

    async def fetch_raw_dailies_for_all_stations(self, headers, time_of_interest):
        return []

    async def fetch_hourlies(self, raw_station, headers, start, end, use_cache, ttl):
        # Default: no hourlies; tests override
        return {"_embedded": {"hourlies": []}}

    async def post_forecasts(self, headers, forecasts_json):
        # simply record or no-op; tests will check session.post call
        return

    async def fetch_stations_by_group_id(self, headers, group_id):
        return []


class FakeEcodivisionSeasons:
    def __init__(self, key, cache):
        self.key = key
        self.cache = cache

    def __enter__(self):
        # return a simple object representing eco division seasonal context
        return object()

    def __exit__(self, exc_type, exc, tb):
        return False

    def get_core_seasons(self):
        return {
            "SUB-ARCTIC HIGHLANDS": {
                "core_season": {
                    "start_month": "6",
                    "start_day": "1",
                    "end_month": "8",
                    "end_day": "15",
                }
            },
            "SUB-ARCTIC": {
                "core_season": {
                    "start_month": "6",
                    "start_day": "1",
                    "end_month": "8",
                    "end_day": "15",
                }
            },
            "BOREAL": {
                "core_season": {
                    "start_month": "5",
                    "start_day": "15",
                    "end_month": "8",
                    "end_day": "31",
                }
            },
            "HUMID CONTINENTAL HIGHLANDS": {
                "core_season": {
                    "start_month": "5",
                    "start_day": "15",
                    "end_month": "8",
                    "end_day": "31",
                }
            },
            "COOL HYPERMARITIME AND HIGHLANDS": {
                "core_season": {
                    "start_month": "5",
                    "start_day": "15",
                    "end_month": "8",
                    "end_day": "31",
                }
            },
            "SEMI-ARID STEPPE HIGHLANDS": {
                "core_season": {
                    "start_month": "5",
                    "start_day": "1",
                    "end_month": "9",
                    "end_day": "15",
                }
            },
            "NORTHEASTERN SUB-ARCTIC PACIFIC": {
                "core_season": {
                    "start_month": "6",
                    "start_day": "1",
                    "end_month": "8",
                    "end_day": "15",
                }
            },
            "DEFAULT": {
                "core_season": {
                    "start_month": "5",
                    "start_day": "1",
                    "end_month": "9",
                    "end_day": "15",
                }
            },
        }


# ---------------------------
# Pytest fixtures
# ---------------------------
@pytest.fixture
def fake_config(monkeypatch):
    # Provide deterministic config values
    def fake_get(key, default=None):
        mapping = {
            "WFWX_BASE_URL": "https://wf1.example",
            "WFWX_AUTH_URL": "https://wf1.example/auth",
            "WFWX_USER": "pytest-user",
            "WFWX_SECRET": "pytest-secret",
            "REDIS_AUTH_CACHE_EXPIRY": "600",
            "REDIS_STATION_CACHE_EXPIRY": "604800",
            "REDIS_HOURLIES_BY_STATION_CODE_CACHE_EXPIRY": "300",
            "REDIS_DAILIES_BY_STATION_CODE_CACHE_EXPIRY": "300",
            "REDIS_USE": "True",  # flip between True/False in tests as needed
        }
        return mapping.get(key, default)

    import wps_shared.config as shared_config

    monkeypatch.setattr(shared_config, "get", fake_get)


@pytest.fixture
def fake_redis(monkeypatch):
    import wps_shared.utils.redis as redis_utils

    def fake_create_redis():
        return object()  # any placeholder

    monkeypatch.setattr(redis_utils, "create_redis", fake_create_redis)


@pytest.fixture
def fake_ecodivision(monkeypatch):
    import wps_wf1.ecodivisions.ecodivision_seasons as eco_mod

    monkeypatch.setattr(eco_mod, "EcodivisionSeasons", FakeEcodivisionSeasons)


@pytest.fixture
def fake_wfwx_client(monkeypatch):
    import wps_wf1.wfwx_api as api_mod

    monkeypatch.setattr(api_mod, "WfwxClient", FakeWfwxClient)


@pytest.fixture
def wfwx_api(fake_config, fake_redis, fake_ecodivision, fake_wfwx_client):
    from aiohttp import ClientSession
    from wps_wf1.wfwx_api import WfwxApi

    session = FakeSession()
    api = WfwxApi(session)
    return api


# ---------------------------
# Unit tests
# ---------------------------


@pytest.mark.anyio
async def test_get_auth_header(wfwx_api):
    header = await wfwx_api._get_auth_header()
    assert header == {"Authorization": "Bearer token123"}


@pytest.mark.anyio
async def test_get_no_cache_auth_header(wfwx_api):
    header = await wfwx_api._get_no_cache_auth_header()
    assert header["Authorization"] == "Bearer token123"
    assert header["Cache-Control"] == "no-cache"


@pytest.mark.anyio
async def test_get_stations_by_codes_filters_and_parses(monkeypatch, wfwx_api):
    # Prepare raw stations
    raw_stations = [
        {
            "id": "1",
            "stationCode": 100,
            "stationStatus": {"id": "ACTIVE"},
            "longitude": -123.1,
            "latitude": 49.1,
        },
        {
            "id": "2",
            "stationCode": 200,
            "stationStatus": {"id": "INACTIVE"},
            "longitude": -123.2,
            "latitude": 49.2,
        },
        {
            "id": "3",
            "stationCode": 300,
            "stationStatus": {"id": "ACTIVE"},
            "longitude": -123.3,
            "latitude": 49.3,
        },
    ]

    # Make the client generator yield our stations
    wfwx_api.wfwx_client.fetch_paged_response_generator = (
        lambda headers, qb, key, use_cache, ttl: async_gen(raw_stations)
    )

    # is_station_valid: True for code 100 and 300, False for 200
    import wps_wf1.util as util_mod

    monkeypatch.setattr(
        util_mod, "is_station_valid", lambda st: st.get("stationStatus", {}).get("id") == "ACTIVE"
    )

    # parse_station returns a simple dict with code
    import wps_wf1.wfwx_api as api_mod

    monkeypatch.setattr(api_mod, "parse_station", lambda st, eco: {"code": st["stationCode"]})

    stations = await wfwx_api.get_stations_by_codes([100, 200, 300])
    assert len(stations) == 2
    assert {s["code"] for s in stations} == {100, 300}


@pytest.mark.anyio
async def test_get_station_data_uses_mapper_and_headers(monkeypatch, wfwx_api):
    # Make generator yield some station items
    items = [{"stationCode": 1}, {"stationCode": 2}]
    wfwx_api.wfwx_client.fetch_paged_response_generator = (
        lambda headers, qb, key, use_cache, ttl: async_gen(items)
    )

    # Mapper that collects items from async generator
    async def mapper(raw_gen):
        collected = []
        async for item in raw_gen:
            collected.append({"parsed": item["stationCode"]})
        return collected

    stations = await wfwx_api.get_station_data(mapper=mapper, use_no_cache_header=True)
    assert stations == [{"parsed": 1}, {"parsed": 2}]


@pytest.mark.anyio
async def test_get_detailed_geojson_stations_filters_inactive(monkeypatch, wfwx_api):
    raw_stations = [
        {
            "id": "A",
            "stationCode": 999,
            "stationStatus": {"id": "ACTIVE"},
            "displayLabel": "S1",
            "longitude": -123.1,
            "latitude": 49.1,
        },
        {
            "id": "B",
            "stationCode": 888,
            "stationStatus": {"id": "INACTIVE"},
            "displayLabel": "S2",
            "longitude": -123.2,
            "latitude": 49.2,
        },
    ]
    wfwx_api.wfwx_client.fetch_paged_response_generator = (
        lambda headers, qb, key, use_cache, ttl: async_gen(raw_stations)
    )

    import wps_wf1.util as util_mod

    monkeypatch.setattr(
        util_mod, "is_station_valid", lambda st: st.get("stationStatus", {}).get("id") == "ACTIVE"
    )

    # Run
    stations, id_to_code = await wfwx_api.get_detailed_geojson_stations(query_builder=object())

    # Only active station present
    assert list(stations.keys()) == [999]
    assert id_to_code == {"A": 999}


@pytest.mark.anyio
async def test_get_detailed_stations_merges_dailies(monkeypatch, wfwx_api):
    # Stub: return station container with expected properties field
    class FakeStationProps:
        def __init__(self, code):
            self.code = code
            self.name = f"Station-{code}"
            self.observations = None
            self.forecasts = None

    class FakeGeoStation:
        def __init__(self, code):
            self.properties = FakeStationProps(code)

    # Patch get_detailed_geojson_stations to return our map and id-code
    async def fake_geo():
        stations_dict = {111: FakeGeoStation(111), 222: FakeGeoStation(222)}
        id_to_code = {"id111": 111, "id222": 222}
        return stations_dict, id_to_code

    monkeypatch.setattr(wfwx_api, "get_detailed_geojson_stations", lambda qb: fake_geo())

    # Patch raw dailies
    dailies = [
        {
            "stationId": "id111",
            "temperature": 20,
            "relativeHumidity": 40,
            "recordType": {"id": "ACTUAL"},
        },
        {
            "stationId": "id222",
            "temperature": 25,
            "relativeHumidity": 35,
            "recordType": {"id": "FORECAST"},
        },
        {
            "stationId": "id222",
            "temperature": 26,
            "relativeHumidity": 33,
            "recordType": {"id": "OTHER"},
        },
        {
            "stationId": "idXYZ",
            "temperature": 30,
            "relativeHumidity": 50,
            "recordType": {"id": "ACTUAL"},
        },  # unknown
    ]

    async def fake_fetch_raw_dailies(headers, toi):
        return dailies

    wfwx_api.wfwx_client.fetch_raw_dailies_for_all_stations = fake_fetch_raw_dailies

    result = await wfwx_api.get_detailed_stations(datetime(2025, 1, 1))
    # We expect two stations
    assert len(result) == 2
    s111 = next(s for s in result if s.properties.code == 111)
    s222 = next(s for s in result if s.properties.code == 222)
    assert s111.properties.observations.temperature == 20
    assert s222.properties.forecasts.temperature == 25
    assert s222.properties.observations is None  # no ACTUAL for station 222


@pytest.mark.anyio
async def test_get_hourly_for_station_filters_actual(monkeypatch, wfwx_api):
    # Hourly payload includes ACTUAL and FORECAST
    payload = {
        "_embedded": {
            "hourlies": [
                {
                    "hourlyMeasurementTypeCode": {"id": "ACTUAL"},
                    "value": 1,
                    "weatherTimestamp": 1_730_000_000_000,  # example ms timestamp
                },
                {
                    "hourlyMeasurementTypeCode": {"id": "FORECAST"},
                    "value": 2,
                    "weatherTimestamp": 1_730_000_000_000,
                },
                {
                    "hourlyMeasurementTypeCode": {"id": "ACTUAL"},
                    "value": 3,
                    "weatherTimestamp": 1_730_000_360_000,
                },
            ]
        }
    }

    async def fake_fetch_hourlies(raw, headers, s, e, use_cache, ttl):
        return payload

    wfwx_api.wfwx_client.fetch_hourlies = fake_fetch_hourlies

    # Patch the symbols used *inside* wps_wf1.wfwx_api (not wps_wf1.parsers),
    # because the module did `from wps_wf1.parsers import parse_*`.
    import wps_wf1.wfwx_api as api_mod

    def fake_parse_hourly(h):
        # Provide at least the required 'datetime' field (and optionally your parsed value)
        ts_ms = h.get("weatherTimestamp")
        dt = datetime.fromtimestamp(ts_ms / 1000.0) if ts_ms is not None else None
        return {
            "datetime": dt,
            "parsed_val": h["value"],  # extra field for test assertions
        }

    def fake_parse_station(rs, eco):
        # Provide required station fields Pydantic expects
        return {
            "code": rs["stationCode"],
            "name": f"Station {rs['stationCode']}",
            "lat": 0.0,
            "long": 0.0,
        }

    monkeypatch.setattr(api_mod, "parse_hourly", fake_parse_hourly)
    monkeypatch.setattr(api_mod, "parse_station", fake_parse_station)

    raw_station = {"stationCode": 123}
    res = await wfwx_api.get_hourly_for_station(
        raw_station,
        start_timestamp=datetime(2025, 1, 1),
        end_timestamp=datetime(2025, 1, 2),
        eco_division=object(),  # OK because parse_station is stubbed
        use_cache=True,
        ttl=60,
    )

    # Filtered to ACTUAL hourlies only
    assert len(res.values) == 2
    assert res.station.code == 123


@pytest.mark.anyio
async def test_get_hourly_readings_runs_tasks(monkeypatch, wfwx_api):
    raw_stations = [{"stationCode": 101}, {"stationCode": 202}]
    wfwx_api.wfwx_client.fetch_paged_response_generator = (
        lambda headers, qb, key, use_cache, ttl: async_gen(raw_stations)
    )

    # stub get_hourly_for_station to return sentinel objects
    async def fake_hourly_for_station(*args, **kwargs):
        raw_station = args[0]
        return f"hourlies-{raw_station['stationCode']}"

    monkeypatch.setattr(wfwx_api, "get_hourly_for_station", fake_hourly_for_station)

    res = await wfwx_api.get_hourly_readings(
        station_codes=[101, 202],
        start_timestamp=datetime(2025, 1, 1),
        end_timestamp=datetime(2025, 1, 2),
        use_cache=True,
    )
    assert res == ["hourlies-101", "hourlies-202"]


@pytest.mark.anyio
async def test_get_noon_forecasts_all_stations(monkeypatch, wfwx_api):
    # Two noon forecast items with stationIds
    noon_items = [
        {"stationId": "wfwx-1", "value": "A"},
        {"stationId": "wfwx-2", "value": "B"},
    ]

    async def async_gen(items):
        for item in items:
            yield item

    # Mock fetch_paged_response_generator to handle both "dailies" and "stations"
    def fake_fetch_paged_response_generator(headers, qb, key, **kwargs):
        if key == "dailies":
            return async_gen(noon_items)
        elif key == "stations":
            return async_gen([])  # station list isn't needed for this test
        return async_gen([])

    wfwx_api.wfwx_client.fetch_paged_response_generator = fake_fetch_paged_response_generator

    # Provide station map (wfwx_id -> code)
    async def fake_wfwx_station_list_mapper(raw_gen):
        # Consume generator to mimic real behavior
        _ = [item async for item in raw_gen]

        class StationObj:
            def __init__(self, wfwx_id, code):
                self.wfwx_id = wfwx_id
                self.code = code

        return [StationObj("wfwx-1", 111), StationObj("wfwx-2", 222)]

    import wps_wf1.wfwx_api as api_mod

    monkeypatch.setattr(api_mod, "wfwx_station_list_mapper", fake_wfwx_station_list_mapper)
    monkeypatch.setattr(
        api_mod,
        "parse_noon_forecast",
        lambda code, nf: {"code": code, "value": nf["value"]} if code == 111 else None,
    )

    res = await wfwx_api.get_noon_forecasts_all_stations(datetime(2025, 1, 1))
    assert res == [{"code": 111, "value": "A"}]


@pytest.mark.anyio
async def test_get_hourly_actuals_all_stations(monkeypatch, wfwx_api):
    # Hourly data returned by WFWX client
    hourly_items = [
        {"stationId": "wfwx-1", "hourlyMeasurementTypeCode": {"id": "ACTUAL"}, "val": 7},
        {"stationId": "wfwx-2", "hourlyMeasurementTypeCode": {"id": "FORECAST"}, "val": 8},
        {"stationId": "wfwx-1", "hourlyMeasurementTypeCode": {"id": "ACTUAL"}, "val": 9},
    ]

    # Provide a generic async generator
    async def async_gen(items):
        for item in items:
            yield item

    # Mock fetch_paged_response_generator so it works for both "hourlies" and "stations"
    def fake_fetch_paged_response_generator(headers, qb, key, **kwargs):
        if key == "hourlies":
            return async_gen(hourly_items)
        elif key == "stations":
            # The mapper we patch below doesn't actually need raw items, but we can return empty
            return async_gen([])  # or return any dummy station payload
        else:
            return async_gen([])

    wfwx_api.wfwx_client.fetch_paged_response_generator = fake_fetch_paged_response_generator

    # Patch the symbols used inside wfwx_api (not in parsers) due to 'from ... import ...' style imports
    import wps_wf1.wfwx_api as api_mod

    async def fake_wfwx_station_list_mapper(raw_gen):
        # Consume the generator (to match real behavior) then return mapping objects
        _ = [item async for item in raw_gen]

        class StationObj:
            def __init__(self, wfwx_id, code):
                self.wfwx_id = wfwx_id
                self.code = code

        return [StationObj("wfwx-1", 111), StationObj("wfwx-2", 222)]

    monkeypatch.setattr(api_mod, "wfwx_station_list_mapper", fake_wfwx_station_list_mapper)
    monkeypatch.setattr(
        api_mod, "parse_hourly_actual", lambda code, h: {"code": code, "val": h["val"]}
    )

    res = await wfwx_api.get_hourly_actuals_all_stations(
        start_timestamp=datetime(2025, 1, 1),
        end_timestamp=datetime(2025, 1, 2),
    )
    # Only ACTUALs for wfwx-1 mapped to code 111
    assert res == [{"code": 111, "val": 7}, {"code": 111, "val": 9}]


@pytest.mark.anyio
async def test_get_wfwx_stations_from_station_codes_none_returns_fire_centre_subset(
    monkeypatch, wfwx_api
):
    # Return a list of stations with code attributes
    async def fake_wfwx_station_list_mapper(raw_gen):
        class StationObj:
            def __init__(self, wfwx_id, code):
                self.wfwx_id = wfwx_id
                self.code = code

        return [StationObj("id-1", 101), StationObj("id-2", 202), StationObj("id-3", 303)]

    import wps_wf1.wfwx_api as api_mod

    monkeypatch.setattr(api_mod, "wfwx_station_list_mapper", fake_wfwx_station_list_mapper)

    res = await wfwx_api.get_wfwx_stations_from_station_codes(
        station_codes=None, fire_centre_station_codes=[101, 303]
    )
    assert [s.code for s in res] == [101, 303]


@pytest.mark.anyio
async def test_get_wfwx_stations_from_station_codes_specific(monkeypatch, wfwx_api, caplog):
    async def fake_wfwx_station_list_mapper(raw_gen):
        class StationObj:
            def __init__(self, wfwx_id, code):
                self.wfwx_id = wfwx_id
                self.code = code

        return [StationObj("id-1", 101), StationObj("id-2", 202)]

    import wps_wf1.wfwx_api as api_mod

    monkeypatch.setattr(api_mod, "wfwx_station_list_mapper", fake_wfwx_station_list_mapper)

    res = await wfwx_api.get_wfwx_stations_from_station_codes(
        station_codes=[101, 999], fire_centre_station_codes=[101, 202]
    )
    assert [s.code for s in res] == [101]
    # The missing one logs an error; we just ensure function doesn’t crash


@pytest.mark.anyio
async def test_get_raw_dailies_in_range_generator(monkeypatch, wfwx_api):
    items = [{"a": 1}, {"b": 2}]
    wfwx_api.wfwx_client.fetch_paged_response_generator = (
        lambda headers, qb, key, use_cache, ttl: async_gen(items)
    )

    gen = await wfwx_api.get_raw_dailies_in_range_generator(
        wfwx_station_ids=["x"], start_timestamp=1, end_timestamp=2
    )
    collected = [i async for i in gen]
    assert collected == items


@pytest.mark.anyio
async def test_get_dailies_generator_flags_and_header(monkeypatch, wfwx_api):
    captured = {"use_cache": None, "ttl": None, "headers_cache_control": None}

    def fake_fetch(headers, qb, key, use_cache, ttl):
        captured["use_cache"] = use_cache
        captured["ttl"] = ttl
        captured["headers_cache_control"] = headers.get("Cache-Control")
        return async_gen([{"dummy": True}])

    wfwx_api.wfwx_client.fetch_paged_response_generator = fake_fetch

    # Case 1: check_cache True, default header
    gen = await wfwx_api.get_dailies_generator(
        wfwx_stations=[types.SimpleNamespace(wfwx_id="A")],
        time_of_interest=datetime(2025, 1, 1),
        end_time_of_interest=datetime(2025, 1, 2),
        check_cache=True,
        use_no_cache_header=False,
    )
    _ = [i async for i in gen]
    assert captured["use_cache"] is True
    assert captured["ttl"] == wfwx_api.wfwx_settings.dailies_by_station_code_expiry
    assert captured["headers_cache_control"] is None

    # Case 2: use_no_cache_header True
    gen = await wfwx_api.get_dailies_generator(
        wfwx_stations=[types.SimpleNamespace(wfwx_id="A")],
        time_of_interest=datetime(2025, 1, 1),
        end_time_of_interest=datetime(2025, 1, 2),
        check_cache=True,
        use_no_cache_header=True,
    )
    _ = [i async for i in gen]
    assert captured["headers_cache_control"] == "no-cache"

    # Case 3: check_cache False
    gen = await wfwx_api.get_dailies_generator(
        wfwx_stations=[types.SimpleNamespace(wfwx_id="A")],
        time_of_interest=datetime(2025, 1, 1),
        end_time_of_interest=datetime(2025, 1, 2),
        check_cache=False,
        use_no_cache_header=False,
    )
    _ = [i async for i in gen]
    assert captured["use_cache"] is False


@pytest.mark.anyio
async def test_get_fire_centers(monkeypatch, wfwx_api):
    # Patch get_station_data to assert mapper is fire_center_mapper and return dict-like
    async def fake_mapper(raw_gen):
        return {"FC1": types.SimpleNamespace(code="FC1"), "FC2": types.SimpleNamespace(code="FC2")}

    # We can invoke directly by patching the mapper reference used
    import wps_wf1.wfwx_api as api_mod

    monkeypatch.setattr(api_mod, "fire_center_mapper", fake_mapper)

    res = await wfwx_api.get_fire_centers()
    assert {fc.code for fc in res} == {"FC1", "FC2"}


@pytest.mark.anyio
async def test_get_dailies_for_stations_and_date(monkeypatch, wfwx_api):
    # Patch station fetch
    async def fake_get_wfwx_stations(*args, **kwargs):
        return [
            types.SimpleNamespace(wfwx_id="A", code=101),
            types.SimpleNamespace(wfwx_id="B", code=202),
        ]

    monkeypatch.setattr(wfwx_api, "get_wfwx_stations_from_station_codes", fake_get_wfwx_stations)

    # Patch dailies generator
    async def fake_dailies_generator(*args, **kwargs):
        return async_gen(
            [
                {
                    "rec": 1,
                    "stationData": {
                        "latitude": 1,
                        "longitude": 1,
                        "recordType": {"id": "ACTIVE"},
                    },
                },
                {
                    "rec": 2,
                    "stationData": {
                        "latitude": 1,
                        "longitude": 1,
                        "recordType": {"id": "ACTIVE"},
                    },
                },
            ]
        )

    monkeypatch.setattr(wfwx_api, "get_dailies_generator", fake_dailies_generator)

    # Mapper returning "ACTUAL" items
    async def fake_mapper(raw_gen, rec_type):
        assert rec_type.name == "ACTUAL"
        items = []
        async for it in raw_gen:
            items.append({"mapped": it["rec"]})
        return items

    res = await wfwx_api.get_dailies_for_stations_and_date(
        start_time_of_interest=datetime(2025, 1, 1),
        end_time_of_interest=datetime(2025, 1, 2),
        unique_station_codes=[101, 202],
        fire_centre_station_codes=[101, 202, 303],
        mapper=fake_mapper,
    )
    assert res == [{"mapped": 1}, {"mapped": 2}]


@pytest.mark.anyio
async def test_get_forecasts_for_stations_by_date_range(monkeypatch, wfwx_api):
    async def fake_get_wfwx_stations(*args, **kwargs):
        return [types.SimpleNamespace(wfwx_id="A", code=101)]

    monkeypatch.setattr(wfwx_api, "get_wfwx_stations_from_station_codes", fake_get_wfwx_stations)

    async def fake_dailies_generator(*args, **kwargs):
        # validate flags forwarded
        assert kwargs["check_cache"] is False
        assert kwargs["use_no_cache_header"] is True
        return async_gen([{"rec": 42}])

    monkeypatch.setattr(wfwx_api, "get_dailies_generator", fake_dailies_generator)

    async def fake_mapper(raw_gen, rec_type):
        assert rec_type.name == "FORECAST"
        items = []
        async for it in raw_gen:
            items.append({"mapped": it["rec"]})
        return items

    res = await wfwx_api.get_forecasts_for_stations_by_date_range(
        start_time_of_interest=datetime(2025, 1, 1),
        end_time_of_interest=datetime(2025, 1, 3),
        unique_station_codes=[101],
        fire_centre_station_codes=[101, 202],
        check_cache=False,
        mapper=fake_mapper,
        use_no_cache_header=True,
    )
    assert res == [{"mapped": 42}]


@pytest.mark.anyio
async def test_get_daily_determinates_for_stations_and_date(monkeypatch, wfwx_api):
    async def fake_get_wfwx_stations(*args, **kwargs):
        return [types.SimpleNamespace(wfwx_id="A", code=101)]

    monkeypatch.setattr(wfwx_api, "get_wfwx_stations_from_station_codes", fake_get_wfwx_stations)

    async def fake_dailies_generator(*args, **kwargs):
        return async_gen([{"rec": "x"}])

    monkeypatch.setattr(wfwx_api, "get_dailies_generator", fake_dailies_generator)

    async def fake_mapper(raw_gen):
        # Consume and return tuple
        _ = [i async for i in raw_gen]
        return (["actuals"], ["forecasts"])

    actuals, forecasts = await wfwx_api.get_daily_determinates_for_stations_and_date(
        start_time_of_interest=datetime(2025, 1, 1),
        end_time_of_interest=datetime(2025, 1, 2),
        unique_station_codes=[101],
        fire_centre_station_codes=[101, 202],
        mapper=fake_mapper,
        check_cache=True,
    )
    assert actuals == ["actuals"]
    assert forecasts == ["forecasts"]


@pytest.mark.anyio
async def test_get_station_groups(monkeypatch, wfwx_api):
    items = [{"group": 1}, {"group": 2}]
    wfwx_api.wfwx_client.fetch_paged_response_generator = lambda headers, qb, key: async_gen(items)

    async def fake_mapper(raw_gen):
        # Map groups out of raw
        res = []
        async for it in raw_gen:
            res.append(it["group"])
        return res

    res = await wfwx_api.get_station_groups(fake_mapper)
    assert res == [1, 2]


@pytest.mark.anyio
async def test_get_stations_by_group_ids(monkeypatch, wfwx_api):
    # For two groups, return different stations
    async def fake_fetch_stations(headers, group_id):
        if group_id == "G1":
            return [{"code": 101}, {"code": 202}]
        else:
            return [{"code": 202}, {"code": 303}]

    wfwx_api.wfwx_client.fetch_stations_by_group_id = fake_fetch_stations

    def fake_mapper(stations):
        # Just return input station codes
        return [s["code"] for s in stations]

    res = await wfwx_api.get_stations_by_group_ids(["G1", "G2"], mapper=fake_mapper)
    assert res == [101, 202, 202, 303]


@pytest.mark.anyio
async def test_post_forecasts(monkeypatch, wfwx_api):
    # Prepare forecasts with model_dump method
    class FakeForecast:
        def __init__(self, payload):
            self.payload = payload
        def model_dump(self):
            return self.payload

    posted = []

    async def fake_post_forecasts(headers, forecasts_json):
        posted.append(("client", forecasts_json))

    wfwx_api.wfwx_client.post_forecasts = fake_post_forecasts

    forecasts = [FakeForecast({"x": 1}), FakeForecast({"y": 2})]
    await wfwx_api.post_forecasts(forecasts)

    # Check client.post_forecasts was called
    assert posted == [("client", [{"x": 1}, {"y": 2}])]

    # Verify session.post was used and raise_for_status invoked
    assert wfwx_api.wfwx_client.session.last_post is not None
    assert wfwx_api.wfwx_client.session.last_post["url"].endswith("/v1/dailies/daily-bulk")
    assert wfwx_api.wfwx_client.session.last_post["json"] == [{"x": 1}, {"y": 2}]
    assert "Authorization" in wfwx_api.wfwx_client.session.last_post["headers"]