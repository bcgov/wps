from unittest.mock import AsyncMock, MagicMock

import pytest
from wps_weather.copy_objects_to_lowercase import copy_to_lowercase

PREFIX = "wx_4panel_charts/"
UPPER_KEY = "wx_4panel_charts/20260407/model_gdps/15km/00/000/GDPS_20260407T00Z_F000_4panel.png"
LOWER_KEY = UPPER_KEY.lower()


def mock_s3_client(keys: list[str]) -> MagicMock:
    async def iter_keys(_prefix):
        for key in keys:
            yield key

    client = MagicMock()
    client.iter_keys = iter_keys
    client.copy_object = AsyncMock()
    client.delete_object = AsyncMock()
    return client


@pytest.mark.anyio
async def test_copies_uppercase_key_and_keeps_original():
    client = mock_s3_client([UPPER_KEY])

    assert await copy_to_lowercase(client, PREFIX) == (1, 0)

    client.copy_object.assert_awaited_once_with(UPPER_KEY, LOWER_KEY)
    client.delete_object.assert_not_awaited()


@pytest.mark.anyio
async def test_skips_key_that_is_already_lowercase():
    client = mock_s3_client([LOWER_KEY])

    assert await copy_to_lowercase(client, PREFIX) == (0, 0)

    client.copy_object.assert_not_awaited()


@pytest.mark.anyio
async def test_skips_key_with_existing_lowercase_copy():
    client = mock_s3_client([UPPER_KEY, LOWER_KEY])

    assert await copy_to_lowercase(client, PREFIX) == (0, 0)

    client.copy_object.assert_not_awaited()


@pytest.mark.anyio
async def test_dry_run_reports_without_copying():
    client = mock_s3_client([UPPER_KEY])

    assert await copy_to_lowercase(client, PREFIX, dry_run=True) == (1, 0)

    client.copy_object.assert_not_awaited()


@pytest.mark.anyio
async def test_failed_copy_is_counted_and_others_continue():
    other_key = UPPER_KEY.replace("F000", "F003")
    client = mock_s3_client([UPPER_KEY, other_key])
    client.copy_object.side_effect = [RuntimeError("copy failed"), None]

    assert await copy_to_lowercase(client, PREFIX) == (1, 1)

    assert client.copy_object.await_count == 2
