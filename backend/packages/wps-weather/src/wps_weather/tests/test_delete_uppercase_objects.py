from unittest.mock import AsyncMock, MagicMock

import pytest
from wps_weather.delete_uppercase_objects import delete_uppercase

PREFIX = "wx_4panel_charts/"
UPPER_KEY = "wx_4panel_charts/20260407/model_gdps/15km/00/000/GDPS_20260407T00Z_F000_4panel.png"
LOWER_KEY = UPPER_KEY.lower()


def mock_s3_client(keys: list[str]) -> MagicMock:
    async def iter_keys(_prefix):
        for key in keys:
            yield key

    client = MagicMock()
    client.iter_keys = iter_keys
    client.delete_object = AsyncMock()
    return client


@pytest.mark.anyio
async def test_deletes_uppercase_key_with_lowercase_copy():
    client = mock_s3_client([UPPER_KEY, LOWER_KEY])

    assert await delete_uppercase(client, PREFIX) == (1, 0, 0)

    client.delete_object.assert_awaited_once_with(UPPER_KEY)


@pytest.mark.anyio
async def test_keeps_uppercase_key_without_lowercase_copy():
    client = mock_s3_client([UPPER_KEY])

    assert await delete_uppercase(client, PREFIX) == (0, 0, 1)

    client.delete_object.assert_not_awaited()


@pytest.mark.anyio
async def test_never_deletes_lowercase_key():
    client = mock_s3_client([LOWER_KEY])

    assert await delete_uppercase(client, PREFIX) == (0, 0, 0)

    client.delete_object.assert_not_awaited()


@pytest.mark.anyio
async def test_dry_run_reports_without_deleting():
    client = mock_s3_client([UPPER_KEY, LOWER_KEY])

    assert await delete_uppercase(client, PREFIX, dry_run=True) == (1, 0, 0)

    client.delete_object.assert_not_awaited()


@pytest.mark.anyio
async def test_failed_delete_is_counted_and_others_continue():
    other_key = UPPER_KEY.replace("F000", "F003")
    client = mock_s3_client([UPPER_KEY, LOWER_KEY, other_key, other_key.lower()])
    client.delete_object.side_effect = [RuntimeError("delete failed"), None]

    assert await delete_uppercase(client, PREFIX) == (1, 1, 0)

    assert client.delete_object.await_count == 2
