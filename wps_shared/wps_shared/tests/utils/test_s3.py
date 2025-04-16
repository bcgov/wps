import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

from wps_shared.utils.s3 import apply_retention_policy_on_date_folders


@pytest.mark.anyio
async def test_retention_policy_dry_run():
    mock_client = AsyncMock()
    bucket = "my-bucket"
    prefix = "data/"
    days_to_retain = 7
    today = datetime.now(timezone.utc).date()

    # 10 days ago (older than retention threshold)
    old_date = (today - timedelta(days=10)).strftime("%Y-%m-%d")

    mock_client.list_objects_v2.side_effect = [
        {"CommonPrefixes": [{"Prefix": f"{prefix}{old_date}/"}]},
        {"Contents": [{"Key": f"{prefix}{old_date}/file1.tif"}, {"Key": f"{prefix}{old_date}/file2.tif"}]},
    ]

    await apply_retention_policy_on_date_folders(
        client=mock_client,
        bucket=bucket,
        prefix=prefix,
        days_to_retain=days_to_retain,
        dry_run=True,
    )

    # list_objects_v2 should be called twice (once for folders, once for object listing)
    assert mock_client.list_objects_v2.call_count == 2
    mock_client.delete_object.assert_not_called()


@pytest.mark.anyio
async def test_retention_policy_actual_deletion():
    mock_client = AsyncMock()
    bucket = "my-bucket"
    prefix = "data/"
    days_to_retain = 7
    today = datetime.now(timezone.utc).date()

    old_date = (today - timedelta(days=10)).strftime("%Y-%m-%d")

    mock_client.list_objects_v2.side_effect = [
        {"CommonPrefixes": [{"Prefix": f"{prefix}{old_date}/"}]},
        {"Contents": [{"Key": f"{prefix}{old_date}/file1.tif"}, {"Key": f"{prefix}{old_date}/file2.tif"}]},
    ]

    await apply_retention_policy_on_date_folders(
        client=mock_client,
        bucket=bucket,
        prefix=prefix,
        days_to_retain=days_to_retain,
        dry_run=False,
    )

    assert mock_client.list_objects_v2.call_count == 2
    assert mock_client.delete_object.await_count == 2
    mock_client.delete_object.assert_any_call(Bucket=bucket, Key=f"{prefix}{old_date}/file1.tif")
    mock_client.delete_object.assert_any_call(Bucket=bucket, Key=f"{prefix}{old_date}/file2.tif")


@pytest.mark.anyio
async def test_retention_policy_ignores_invalid_date_prefix():
    mock_client = AsyncMock()
    bucket = "my-bucket"
    prefix = "data/"

    mock_client.list_objects_v2.return_value = {"CommonPrefixes": [{"Prefix": f"{prefix}not-a-date-folder/"}]}

    await apply_retention_policy_on_date_folders(
        client=mock_client,
        bucket=bucket,
        prefix=prefix,
        days_to_retain=7,
        dry_run=False,
    )

    mock_client.list_objects_v2.assert_called_once()
    mock_client.delete_object.assert_not_called()
