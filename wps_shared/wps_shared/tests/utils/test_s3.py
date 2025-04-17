import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

from wps_shared.utils.s3 import apply_retention_policy_on_date_folders


def setup_test_vars():
    bucket = "my-bucket"
    prefix = "data/"
    today = datetime.now(timezone.utc).date()
    mock_client = AsyncMock()
    return bucket, prefix, today, mock_client


@pytest.mark.anyio
async def test_retention_policy_dry_run_does_not_delete():
    bucket, prefix, today, mock_client = setup_test_vars()
    folder_date = today - timedelta(days=10)
    folder_prefix = f"{prefix}{folder_date.strftime('%Y-%m-%d')}/"

    mock_client.list_objects_v2.side_effect = [
        {"CommonPrefixes": [{"Prefix": folder_prefix}]},
        {
            "Contents": [
                {"Key": f"{folder_prefix}file1.tif"},
                {"Key": f"{folder_prefix}file2.tif"},
            ]
        },
    ]

    await apply_retention_policy_on_date_folders(
        client=mock_client,
        bucket=bucket,
        prefix=prefix,
        days_to_retain=7,
        dry_run=True,
    )

    assert mock_client.list_objects_v2.call_count == 2
    mock_client.delete_object.assert_not_called()


@pytest.mark.anyio
async def test_retention_policy_deletes_old_data():
    bucket, prefix, today, mock_client = setup_test_vars()
    folder_date = today - timedelta(days=10)
    folder_prefix = f"{prefix}{folder_date.strftime('%Y-%m-%d')}/"

    mock_client.list_objects_v2.side_effect = [
        {"CommonPrefixes": [{"Prefix": folder_prefix}]},
        {
            "Contents": [
                {"Key": f"{folder_prefix}file1.tif"},
                {"Key": f"{folder_prefix}file2.tif"},
            ]
        },
    ]

    await apply_retention_policy_on_date_folders(
        client=mock_client,
        bucket=bucket,
        prefix=prefix,
        days_to_retain=7,
        dry_run=False,
    )

    assert mock_client.list_objects_v2.call_count == 2
    assert mock_client.delete_object.await_count == 2
    mock_client.delete_object.assert_any_call(Bucket=bucket, Key=f"{folder_prefix}file1.tif")
    mock_client.delete_object.assert_any_call(Bucket=bucket, Key=f"{folder_prefix}file2.tif")


@pytest.mark.anyio
async def test_retention_policy_ignores_invalid_date_prefix():
    bucket, prefix, _, mock_client = setup_test_vars()

    mock_client.list_objects_v2.return_value = {"CommonPrefixes": [{"Prefix": f"{prefix}not-a-date/"}]}

    await apply_retention_policy_on_date_folders(
        client=mock_client,
        bucket=bucket,
        prefix=prefix,
        days_to_retain=7,
        dry_run=False,
    )

    mock_client.list_objects_v2.assert_called_once()
    mock_client.delete_object.assert_not_called()
