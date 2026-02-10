from datetime import date, datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest

from wps_shared.utils.s3 import apply_retention_policy_on_date_folders, extract_date_from_prefix
from wps_shared.utils.s3_client import S3Client
from wps_shared.utils.time import get_utc_now


@pytest.fixture
def s3_client_mock():
    mock = AsyncMock(spec=S3Client)
    mock.bucket = "my-bucket"
    yield mock


@pytest.fixture
def test_vars():
    bucket = "my-bucket"
    prefix = "data/"
    today = datetime.now(timezone.utc).date()
    mock_client = AsyncMock()
    return bucket, prefix, today, mock_client


@pytest.fixture
def old_folder_prefix():
    today = get_utc_now().date()
    folder_date = today - timedelta(days=10)
    return f"data/{folder_date.strftime('%Y-%m-%d')}/"


@pytest.mark.anyio
async def test_retention_policy_dry_run_does_not_delete(s3_client_mock, old_folder_prefix):
    # Mock iter_common_prefixes to yield the folder
    s3_client_mock.iter_common_prefixes.return_value.__aiter__.return_value = [old_folder_prefix]

    # Mock iter_keys to yield some object keys
    s3_client_mock.iter_keys.return_value.__aiter__.return_value = [
        f"{old_folder_prefix}file1.tif",
        f"{old_folder_prefix}file2.tif",
    ]

    await apply_retention_policy_on_date_folders(
        client=s3_client_mock,
        prefix="data/",
        days_to_retain=7,
        dry_run=True,
    )

    s3_client_mock.delete_prefix.assert_called_once_with(old_folder_prefix, dry_run=True)


@pytest.mark.anyio
async def test_retention_policy_deletes_old_data(s3_client_mock, old_folder_prefix):
    s3_client_mock.iter_common_prefixes.return_value.__aiter__.return_value = [old_folder_prefix]
    s3_client_mock.iter_keys.return_value.__aiter__.return_value = [
        f"{old_folder_prefix}file1.tif",
        f"{old_folder_prefix}file2.tif",
    ]

    # Patch delete_prefix to just return number of objects deleted
    s3_client_mock.delete_prefix.return_value = 2

    await apply_retention_policy_on_date_folders(
        client=s3_client_mock,
        prefix="data/",
        days_to_retain=7,
        dry_run=False,
    )

    s3_client_mock.delete_prefix.assert_called_once_with(old_folder_prefix, dry_run=False)


@pytest.mark.anyio
async def test_retention_policy_ignores_invalid_date_prefix(s3_client_mock):
    # Mock an invalid prefix that doesn't parse as a date
    invalid_prefix = "data/not-a-date/"
    s3_client_mock.iter_common_prefixes.return_value.__aiter__.return_value = [invalid_prefix]

    await apply_retention_policy_on_date_folders(
        client=s3_client_mock,
        prefix="data/",
        days_to_retain=7,
        dry_run=False,
    )

    # delete_prefix should never be called
    s3_client_mock.delete_prefix.assert_not_called()


@pytest.mark.parametrize(
    "folder_prefix,base_prefix,expected",
    [
        ("data/2024-06-01/", "data/", date(2024, 6, 1)),
        ("data/2023-01-15/somefile", "data/", date(2023, 1, 15)),
        ("prefix/2022-12-31/", "prefix/", date(2022, 12, 31)),
        ("prefix/2022-12-31/extra/", "prefix/", date(2022, 12, 31)),
        ("foo/bar/20200229/", "foo/bar/", date(2020, 2, 29)),
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
        ("data/2024-06-01/", "wrongprefix/"),  # base_prefix not matching
    ],
)
def test_extract_date_from_prefix_invalid(folder_prefix, base_prefix):
    assert extract_date_from_prefix(folder_prefix, base_prefix) is None
