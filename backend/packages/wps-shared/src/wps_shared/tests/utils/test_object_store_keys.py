"""Tests for the opt-in OBJECT_STORE_KEY_PREFIX helper."""

import pytest
from wps_shared.utils.object_store_keys import (
    get_object_store_key_prefix,
    object_store_gdal_path,
    object_store_key,
)

UNPREFIXED_KEY = "sfms/uploads/actual/2024-10-10/hfi20241010.tif"


@pytest.mark.parametrize("value", [None, "", "  ", "/", "//"])
def test_prefix_unset_or_empty_leaves_keys_byte_identical(monkeypatch, value):
    if value is None:
        monkeypatch.delenv("OBJECT_STORE_KEY_PREFIX", raising=False)
    else:
        monkeypatch.setenv("OBJECT_STORE_KEY_PREFIX", value)

    assert get_object_store_key_prefix() == ""
    # Byte-identical (same object) when the prefix is unset or empty.
    assert object_store_key(UNPREFIXED_KEY) is UNPREFIXED_KEY
    assert object_store_key(UNPREFIXED_KEY) == "sfms/uploads/actual/2024-10-10/hfi20241010.tif"
    assert object_store_gdal_path(UNPREFIXED_KEY, bucket="some bucket") == (
        f"/vsis3/some bucket/{UNPREFIXED_KEY}"
    )


@pytest.mark.parametrize(
    "raw, expected_prefix",
    [
        ("local/tester", "local/tester/"),
        ("local/tester/", "local/tester/"),
        ("  local/tester/  ", "local/tester/"),
        ("/local/tester/", "local/tester/"),
        ("local/tester//", "local/tester/"),
    ],
)
def test_trailing_slash_normalization(monkeypatch, raw, expected_prefix):
    monkeypatch.setenv("OBJECT_STORE_KEY_PREFIX", raw)
    assert get_object_store_key_prefix() == expected_prefix
    assert object_store_key(UNPREFIXED_KEY) == f"{expected_prefix}{UNPREFIXED_KEY}"
    already = f"{expected_prefix}{UNPREFIXED_KEY}"
    assert object_store_key(already) == already
    assert object_store_gdal_path(UNPREFIXED_KEY, bucket="some bucket") == (
        f"/vsis3/some bucket/{expected_prefix}{UNPREFIXED_KEY}"
    )


def test_prefix_lookup_ignores_one_arg_config_get_stub(monkeypatch):
    """Jobs tests stub config.get as a one-arg lambda on the shared module."""
    monkeypatch.delenv("OBJECT_STORE_KEY_PREFIX", raising=False)
    import wps_shared.config as shared_config

    monkeypatch.setattr(shared_config, "get", lambda _key: "classified_tpi.tif")
    assert object_store_key(UNPREFIXED_KEY) is UNPREFIXED_KEY
    monkeypatch.setenv("OBJECT_STORE_KEY_PREFIX", "local/tester")
    assert object_store_key(UNPREFIXED_KEY) == f"local/tester/{UNPREFIXED_KEY}"
