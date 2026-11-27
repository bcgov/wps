"""OBJECT_STORE_KEY_PREFIX coverage for critical-hours object keys."""

from datetime import date

from app.auto_spatial_advisory.critical_hours_key import get_critical_hours_key

UNSET_KEY = "critical_hours/2024-10-10/42_critical_hours.json"


def test_critical_hours_key_unchanged_when_prefix_unset(monkeypatch):
    monkeypatch.delenv("OBJECT_STORE_KEY_PREFIX", raising=False)
    assert get_critical_hours_key(date(2024, 10, 10), 42) == UNSET_KEY


def test_critical_hours_key_prefixed_when_set(monkeypatch):
    monkeypatch.setenv("OBJECT_STORE_KEY_PREFIX", "local/tester")
    assert get_critical_hours_key(date(2024, 10, 10), 42) == f"local/tester/{UNSET_KEY}"
