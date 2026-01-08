
# test_wfwx_api_factory.py
import asyncio
import pytest
from unittest.mock import Mock

from aiohttp import ClientSession

from wps_shared.wildfire_one.wfwx_api import create_wfwx_api


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


@pytest.mark.anyio
async def test_create_wfwx_api_happy_path(monkeypatch, aiohttp_session):
    """
    Given full config values and REDIS_USE == "True",
    the factory should construct WfwxSettings correctly,
    call create_redis once, and instantiate WfwxApi with
    (session, settings, cache).
    """
    # Arrange: config values
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

    # Patch config.get
    from wps_shared import config as shared_config
    monkeypatch.setattr(shared_config, "get", make_config_get_stub(cfg))

    # Patch create_redis to return a sentinel cache
    from wps_shared.utils import redis as redis_utils
    cache_sentinel = object()
    create_redis_spy = Mock(return_value=cache_sentinel)
    monkeypatch.setattr(redis_utils, "create_redis", create_redis_spy)

    # Patch WfwxApi to capture init args and return a sentinel instance
    from wps_wf1.wfwx_api import WfwxApi as RealWfwxApi
    wfwx_api_instance = object()

    def wfwxapi_ctor(*, session, wfwx_settings, cache):
        # Basic shape checks on passed settings
        assert isinstance(session, ClientSession)
        assert wfwx_settings.base_url == cfg["WFWX_BASE_URL"]
        assert wfwx_settings.auth_url == cfg["WFWX_AUTH_URL"]
        assert wfwx_settings.user == cfg["WFWX_USER"]
        assert wfwx_settings.secret == cfg["WFWX_SECRET"]
        assert wfwx_settings.auth_cache_expiry == int(cfg["REDIS_AUTH_CACHE_EXPIRY"])
        assert wfwx_settings.station_cache_expiry == int(cfg["REDIS_STATION_CACHE_EXPIRY"])
        assert wfwx_settings.hourlies_by_station_code_expiry == int(
            cfg["REDIS_HOURLIES_BY_STATION_CODE_CACHE_EXPIRY"]
        )
        assert wfwx_settings.dailies_by_station_code_expiry == int(
            cfg["REDIS_DAILIES_BY_STATION_CODE_CACHE_EXPIRY"]
        )
        assert wfwx_settings.use_cache is True
        assert cache is cache_sentinel
        return wfwx_api_instance

    monkeypatch.setattr(
        RealWfwxApi, "__call__", lambda *args, **kwargs: wfwxapi_ctor(**kwargs)
    )
    # Alternatively, simpler: monkeypatch the class name itself
    monkeypatch.setattr(
        "wps_wf1.wfwx_api.WfwxApi",
        lambda *, session, wfwx_settings, cache: wfwxapi_ctor(
            session=session, wfwx_settings=wfwx_settings, cache=cache
        ),
    )

    # Act
    result = create_wfwx_api(session=aiohttp_session)

    # Assert
    assert result is wfwx_api_instance
    create_redis_spy.assert_called_once()


@pytest.mark.asyncio
async def test_create_wfwx_api_defaults_and_use_cache_false(monkeypatch, aiohttp_session):
    """
    When some expiry keys are missing and REDIS_USE is not 'True',
    defaults are applied and use_cache becomes False.
    """
    # Provide only required keys, omit expiry keys to force defaults.
    cfg = {
        "WFWX_BASE_URL": "https://api.example.com/wfwx",
        "WFWX_AUTH_URL": "https://auth.example.com/oauth",
        "WFWX_USER": "wfwx-user",
        "WFWX_SECRET": "super-secret",
        # Deliberately omit REDIS_*_EXPIRY to hit defaults.
        "REDIS_USE": "False",  # anything not "True" should be False
    }

    # Patch config.get
    from wps_shared import config as shared_config
    monkeypatch.setattr(shared_config, "get", make_config_get_stub(cfg))

    # Patch create_redis
    from wps_shared.utils import redis as redis_utils
    cache_sentinel = object()
    create_redis_spy = Mock(return_value=cache_sentinel)
    monkeypatch.setattr(redis_utils, "create_redis", create_redis_spy)

    # Patch WfwxApi ctor
    from wps_wf1.wfwx_api import WfwxApi as RealWfwxApi
    wfwx_api_instance = object()

    def wfwxapi_ctor(*, session, wfwx_settings, cache):
        assert isinstance(session, ClientSession)
        assert wfwx_settings.base_url == cfg["WFWX_BASE_URL"]
        assert wfwx_settings.auth_url == cfg["WFWX_AUTH_URL"]
        assert wfwx_settings.user == cfg["WFWX_USER"]
        assert wfwx_settings.secret == cfg["WFWX_SECRET"]
        # Defaults from the factory code:
        assert wfwx_settings.auth_cache_expiry == 600
        assert wfwx_settings.station_cache_expiry == 604800
        assert wfwx_settings.hourlies_by_station_code_expiry == 300
        assert wfwx_settings.dailies_by_station_code_expiry == 300
        assert wfwx_settings.use_cache is False
        assert cache is cache_sentinel
        return wfwx_api_instance

    monkeypatch.setattr(
        "wps_wf1.wfwx_api.WfwxApi",
        lambda *, session, wfwx_settings, cache: wfwxapi_ctor(
            session=session, wfwx_settings=wfwx_settings, cache=cache
        ),
    )

    # Act
    result = create_wfwx_api(session=aiohttp_session)

    # Assert
    assert result is wfwx_api_instance
    create_redis_spy.assert_called_once()


@pytest.mark.asyncio
async def test_create_wfwx_api_redis_use_truthy_only(monkeypatch, aiohttp_session):
    """
    Validate that only 'True' (string) sets use_cache=True. Other truthy-looking values
    like 'true', '1', True should be treated as False by the factory logic.
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

        # Patch config.get per iteration
        from wps_shared import config as shared_config
        monkeypatch.setattr(shared_config, "get", make_config_get_stub(cfg))

        # Patch create_redis
        from wps_shared.utils import redis as redis_utils
        cache_sentinel = object()
        create_redis_spy = Mock(return_value=cache_sentinel)
        monkeypatch.setattr(redis_utils, "create_redis", create_redis_spy)

        # Patch WfwxApi ctor
        from wps_wf1.wfwx_api import WfwxApi as RealWfwxApi
        wfwx_api_instance = object()

        def wfwxapi_ctor(*, session, wfwx_settings, cache):
            assert isinstance(session, ClientSession)
            assert wfwx_settings.use_cache is expected
            return wfwx_api_instance

        monkeypatch.setattr(
            "wps_wf1.wfwx_api.WfwxApi",
            lambda *, session, wfwx_settings, cache: wfwxapi_ctor(
                session=session, wfwx_settings=wfwx_settings, cache=cache
            ),
        )

        # Act
        result = create_wfwx_api(session=aiohttp_session)

        # Assert
        assert result is wfwx_api_instance
        create_redis_spy.assert_called_once()

        # Reset the spy between iterations
        create_redis_spy.reset_mock()
