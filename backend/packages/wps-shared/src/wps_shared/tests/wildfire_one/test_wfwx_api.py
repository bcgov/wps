
# test_wfwx_api_factory.py
import pytest
from aiohttp import ClientSession

# Import the module under test as a namespace, so we can patch its local symbols.
import wps_shared.wildfire_one.wfwx_api as factory


@pytest.fixture
async def aiohttp_session():
    """Create and cleanup a real aiohttp ClientSession for the factory."""
    session = ClientSession()
    try:
        yield session
    finally:
        await session.close()


def make_config_get_stub(values: dict):
    """
    Returns a stub function that mimics config.get(key, default=None)
    using `values` dict. Missing keys return the provided `default`.
    """
    def _get(key, default=None):
        return values.get(key, default)
    return _get


class DummyApi:
    """Deterministic stub for WfwxApi that captures ctor args."""

    def __init__(self, *, session, wfwx_settings, cache):
        self.session = session
        self.settings = wfwx_settings
        self.cache = cache


@pytest.mark.anyio
async def test_create_wfwx_api_happy_path(monkeypatch, aiohttp_session):
    """
    With full config and REDIS_USE == 'True', factory builds settings correctly
    and wires session+cache into WfwxApi.
    """
    cfg = {
        "WFWX_BASE_URL": "https://api.example.com/wfwx",
        "WFWX_AUTH_URL": "https://auth.example.com/oauth",
        "WFWX_USER": "wfwx-user",
        "WFWX_SECRET": "super-secret",
        "REDIS_AUTH_CACHE_EXPIRY": "900",
        "REDIS_STATION_CACHE_EXPIRY": "86400",
        "REDIS_HOURLIES_BY_STATION_CODE_CACHE_EXPIRY": "120",
        "REDIS_DAILIES_BY_STATION_CODE_CACHE_EXPIRY": "180",
        "REDIS_USE": "True",
    }

    # Patch symbols WHERE THEY ARE USED: in the factory module.
    monkeypatch.setattr(factory.config, "get", make_config_get_stub(cfg))

    cache_sentinel = object()
    monkeypatch.setattr(factory, "create_redis", lambda: cache_sentinel)

    # Replace the class with our deterministic stub.
    monkeypatch.setattr(factory, "WfwxApi", DummyApi)

    # Act
    result = factory.create_wfwx_api(session=aiohttp_session)

    # Assert: result is our DummyApi instance with captured args.
    assert isinstance(result, DummyApi)
    assert result.session is aiohttp_session
    assert result.cache is cache_sentinel

    s = result.settings
    assert s.base_url == cfg["WFWX_BASE_URL"]
    assert s.auth_url == cfg["WFWX_AUTH_URL"]
    assert s.user == cfg["WFWX_USER"]
    assert s.secret == cfg["WFWX_SECRET"]
    assert s.auth_cache_expiry == int(cfg["REDIS_AUTH_CACHE_EXPIRY"])
    assert s.station_cache_expiry == int(cfg["REDIS_STATION_CACHE_EXPIRY"])
    assert s.hourlies_by_station_code_expiry == int(
        cfg["REDIS_HOURLIES_BY_STATION_CODE_CACHE_EXPIRY"]
    )
    assert s.dailies_by_station_code_expiry == int(
        cfg["REDIS_DAILIES_BY_STATION_CODE_CACHE_EXPIRY"]
    )
    assert s.use_cache is True


@pytest.mark.anyio
async def test_create_wfwx_api_defaults_and_use_cache_false(monkeypatch, aiohttp_session):
    """
    When expiry keys are missing and REDIS_USE != 'True', defaults apply and use_cache=False.
    """
    cfg = {
        "WFWX_BASE_URL": "https://api.example.com/wfwx",
        "WFWX_AUTH_URL": "https://auth.example.com/oauth",
        "WFWX_USER": "wfwx-user",
        "WFWX_SECRET": "super-secret",
        "REDIS_USE": "False",
    }

    monkeypatch.setattr(factory.config, "get", make_config_get_stub(cfg))
    cache_sentinel = object()
    monkeypatch.setattr(factory, "create_redis", lambda: cache_sentinel)
    monkeypatch.setattr(factory, "WfwxApi", DummyApi)

    result = factory.create_wfwx_api(session=aiohttp_session)

    assert isinstance(result, DummyApi)
    assert result.session is aiohttp_session
    assert result.cache is cache_sentinel

    s = result.settings
    # Defaults from the factory code:
    assert s.auth_cache_expiry == 600
    assert s.station_cache_expiry == 604800
    assert s.hourlies_by_station_code_expiry == 300
    assert s.dailies_by_station_code_expiry == 300
    assert s.use_cache is False


@pytest.mark.anyio
async def test_create_wfwx_api_redis_use_truthy_only(monkeypatch, aiohttp_session):
    """
    Only the exact string 'True' sets use_cache=True; other values become False.
    """
    for value, expected in [
        ("True", True),
        ("true", False),
        ("1", False),
        ("", False),
        (None, False),
    ]:
        cfg = {
            "WFWX_BASE_URL": "https://api.example.com/wfwx",
            "WFWX_AUTH_URL": "https://auth.example.com/oauth",
            "WFWX_USER": "wfwx-user",
            "WFWX_SECRET": "super-secret",
            "REDIS_USE": value,
        }

        monkeypatch.setattr(factory.config, "get", make_config_get_stub(cfg))
        cache_sentinel = object()
        monkeypatch.setattr(factory, "create_redis", lambda: cache_sentinel)
        monkeypatch.setattr(factory, "WfwxApi", DummyApi)

        result = factory.create_wfwx_api(session=aiohttp_session)

        assert isinstance(result, DummyApi)
        assert result.settings.use_cache is expected
