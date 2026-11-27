"""OBJECT_STORE_KEY_PREFIX coverage for weather job prefixes."""

import os

# s3_data_retention reads these at import time.
os.environ.setdefault("GRIB_RETENTION_THRESHOLD", "2")
os.environ.setdefault("WX_OBJECT_STORE_BUCKET", "wx-bucket")
os.environ.setdefault("WX_OBJECT_STORE_USER_ID", "wx-user")
os.environ.setdefault("WX_OBJECT_STORE_SECRET", "wx-secret")

from wps_weather.eccc_consumer_runner import resolve_s3_prefix
from wps_weather.s3_data_retention import get_grib_retention_prefix

UNSET_PREFIX = "weather_models/"


def test_grib_retention_prefix_unchanged_when_unset(monkeypatch):
    monkeypatch.delenv("OBJECT_STORE_KEY_PREFIX", raising=False)
    assert get_grib_retention_prefix() == UNSET_PREFIX


def test_grib_retention_prefix_prefixed_when_set(monkeypatch):
    monkeypatch.setenv("OBJECT_STORE_KEY_PREFIX", "local/tester")
    assert get_grib_retention_prefix() == f"local/tester/{UNSET_PREFIX}"


def test_eccc_s3_prefix_unchanged_when_unset(monkeypatch):
    monkeypatch.delenv("OBJECT_STORE_KEY_PREFIX", raising=False)
    assert resolve_s3_prefix("weather_models/") == UNSET_PREFIX


def test_eccc_s3_prefix_prefixed_when_set(monkeypatch):
    monkeypatch.setenv("OBJECT_STORE_KEY_PREFIX", "local/tester")
    assert resolve_s3_prefix("weather_models/") == f"local/tester/{UNSET_PREFIX}"
