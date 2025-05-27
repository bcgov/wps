from datetime import date, datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest

from wps_shared.utils.s3 import apply_retention_policy_on_date_folders, extract_date_from_prefix


@pytest.fixture
def test_vars():
    bucket = "my-bucket"
    prefix = "data/"
    today = datetime.now(timezone.utc).date()
    mock_client = AsyncMock()
    return bucket, prefix, today, mock_client


@pytest.fixture
def old_folder_prefix(test_vars):
    _, prefix, today, _ = test_vars
    folder_date = today - timedelta(days=10)
    return f"{prefix}{folder_date.strftime('%Y-%m-%d')}/"


@pytest.mark.anyio
async def test_retention_policy_dry_run_does_not_delete(test_vars, old_folder_prefix):
    bucket, prefix, _, mock_client = test_vars

    mock_client.list_objects_v2.side_effect = [
        {"CommonPrefixes": [{"Prefix": old_folder_prefix}]},
        {
            "Contents": [
                {"Key": f"{old_folder_prefix}file1.tif"},
                {"Key": f"{old_folder_prefix}file2.tif"},
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
async def test_retention_policy_deletes_old_data(test_vars, old_folder_prefix):
    bucket, prefix, _, mock_client = test_vars

    mock_client.list_objects_v2.side_effect = [
        {"CommonPrefixes": [{"Prefix": old_folder_prefix}]},
        {
            "Contents": [
                {"Key": f"{old_folder_prefix}file1.tif"},
                {"Key": f"{old_folder_prefix}file2.tif"},
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
    mock_client.delete_object.assert_any_call(Bucket=bucket, Key=f"{old_folder_prefix}file1.tif")
    mock_client.delete_object.assert_any_call(Bucket=bucket, Key=f"{old_folder_prefix}file2.tif")


@pytest.mark.anyio
async def test_retention_policy_ignores_invalid_date_prefix(test_vars):
    bucket, prefix, _, mock_client = test_vars

    mock_client.list_objects_v2.return_value = {
        "CommonPrefixes": [{"Prefix": f"{prefix}not-a-date/"}]
    }

    await apply_retention_policy_on_date_folders(
        client=mock_client,
        bucket=bucket,
        prefix=prefix,
        days_to_retain=7,
        dry_run=False,
    )

    mock_client.list_objects_v2.assert_called_once()
    mock_client.delete_object.assert_not_called()


@pytest.mark.parametrize(
    "folder_prefix,base_prefix,expected",
    [
        ("data/2024-06-01/", "data/", date(2024, 6, 1)),
        ("data/2023-01-15/somefile", "data/", date(2023, 1, 15)),
        ("prefix/2022-12-31/", "prefix/", date(2022, 12, 31)),
        ("prefix/2022-12-31/extra/", "prefix/", date(2022, 12, 31)),
        ("foo/bar/2020-02-29/", "foo/bar/", date(2020, 2, 29)),
    ],
)
def test_extract_date_from_prefix_valid(folder_prefix, base_prefix, expected):
    assert extract_date_from_prefix(folder_prefix, base_prefix) == expected


@pytest.mark.parametrize(
    "folder_prefix,base_prefix",
    [
        ("data/not-a-date/", "data/"),
        ("data/2024-13-01/", "data/"),  # invalid month
        ("data/2024-06-32/", "data/"),  # invalid day
        ("data/", "data/"),
        ("data//", "data/"),
        ("data/20240601/", "data/"),  # wrong format
        ("data/2024-06-01/", "wrongprefix/"),  # base_prefix not matching
    ],
)
def test_extract_date_from_prefix_invalid(folder_prefix, base_prefix):
    assert extract_date_from_prefix(folder_prefix, base_prefix) is None
