from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from wps_shared.db.crud.weather_models import get_model_and_run_timestamp
from wps_shared.weather_models import ModelEnum

RUN_TS = datetime(2026, 11, 17, 0, tzinfo=UTC)


def session_returning(row):
    result = MagicMock()
    result.one_or_none.return_value = row
    session = MagicMock()
    session.execute = AsyncMock(return_value=result)
    return session


@pytest.mark.anyio
async def test_returns_the_model_and_run_timestamp():
    session = session_returning(
        SimpleNamespace(abbreviation="ECMWF", prediction_run_timestamp=RUN_TS)
    )

    assert await get_model_and_run_timestamp(session, 42) == (ModelEnum.ECMWF, RUN_TS)


@pytest.mark.anyio
async def test_returns_none_when_there_is_no_such_run():
    session = session_returning(None)

    assert await get_model_and_run_timestamp(session, 42) is None
