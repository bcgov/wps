"""OBJECT_STORE_KEY_PREFIX coverage for API utility key builders."""

from datetime import UTC, date, datetime

from app.auto_spatial_advisory.common import get_hfi_s3_key
from app.utils.sfms import get_hourly_filename, get_target_filename
from wps_shared.run_type import RunType

# 06:00 UTC on 2024-10-10 is 23:00 PDT on 2024-10-09.
TEST_DT = datetime(2024, 10, 10, 6, tzinfo=UTC)
UNSET_HFI = "/vsis3/some bucket/sfms/uploads/forecast/2024-10-09/hfi20241010.tif"


def test_hfi_key_unchanged_when_prefix_unset(monkeypatch):
    monkeypatch.delenv("OBJECT_STORE_KEY_PREFIX", raising=False)
    monkeypatch.setenv("OBJECT_STORE_BUCKET", "some bucket")
    assert get_hfi_s3_key(RunType.FORECAST, TEST_DT, date(2024, 10, 10)) == UNSET_HFI


def test_hfi_and_sfms_filenames_prefixed_when_set(monkeypatch):
    monkeypatch.setenv("OBJECT_STORE_KEY_PREFIX", "local/tester")
    monkeypatch.setenv("OBJECT_STORE_BUCKET", "some bucket")
    assert get_hfi_s3_key(RunType.FORECAST, TEST_DT, date(2024, 10, 10)) == (
        "/vsis3/some bucket/local/tester/sfms/uploads/forecast/2024-10-09/hfi20241010.tif"
    )
    target = get_target_filename("hfi20241010.tif")
    assert target.startswith("local/tester/sfms/uploads/")
    hourly = get_hourly_filename("hfi20241010-04.tif")
    assert hourly.startswith("local/tester/sfms/uploads/hourlies/")


def test_hfi_key_normalizes_trailing_slash(monkeypatch):
    monkeypatch.setenv("OBJECT_STORE_KEY_PREFIX", "local/tester/")
    monkeypatch.setenv("OBJECT_STORE_BUCKET", "some bucket")
    assert get_hfi_s3_key(RunType.FORECAST, TEST_DT, date(2024, 10, 10)) == (
        "/vsis3/some bucket/local/tester/sfms/uploads/forecast/2024-10-09/hfi20241010.tif"
    )
