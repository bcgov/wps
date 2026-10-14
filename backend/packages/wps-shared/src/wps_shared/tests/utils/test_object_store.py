import pytest

from wps_shared.utils.object_store import (
    get_endpoint_url,
    get_gdal_endpoint,
    is_loopback_endpoint,
    normalize_endpoint_url,
)


def test_get_endpoint_url_accepts_full_url():
    assert get_endpoint_url("http://127.0.0.1:9000/") == "http://127.0.0.1:9000"


def test_get_endpoint_url_preserves_legacy_https_server(mocker):
    mocker.patch("wps_shared.utils.object_store.get_config", return_value=None)

    assert get_endpoint_url("objects.example.com") == "https://objects.example.com"


def test_get_gdal_endpoint_for_local_http(mocker):
    mocker.patch(
        "wps_shared.utils.object_store.get_config",
        return_value="http://127.0.0.1:9000",
    )

    assert get_gdal_endpoint() == ("127.0.0.1:9000", False)


@pytest.mark.parametrize(
    "endpoint_url",
    [
        "http://localhost:9000",
        "http://127.0.0.1:9000",
        "http://[::1]:9000",
    ],
)
def test_loopback_endpoints(endpoint_url):
    assert is_loopback_endpoint(endpoint_url)


def test_remote_endpoint_is_not_loopback():
    assert not is_loopback_endpoint("https://objects.example.com")


@pytest.mark.parametrize(
    "endpoint_url",
    [
        "127.0.0.1:9000",
        "ftp://127.0.0.1:9000",
        "http://127.0.0.1:9000/a/path",
    ],
)
def test_invalid_endpoint_urls(endpoint_url):
    with pytest.raises(ValueError):
        normalize_endpoint_url(endpoint_url)
