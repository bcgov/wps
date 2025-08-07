from datetime import datetime, timezone

import pytest
from sqlalchemy.future import select

from wps_shared.db.crud.auto_spatial_advisory import mark_run_parameter_complete
from wps_shared.db.models.auto_spatial_advisory import Base, RunParameters
from wps_shared.run_type import RunType


@pytest.mark.anyio
async def test_mark_run_parameter_complete(db_session, session_factory):
    run_datetime = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    for_date = run_datetime.date()

    run_param = RunParameters(
        run_type=RunType.FORECAST.value,
        run_datetime=run_datetime,
        for_date=for_date,
        complete=False,
    )
    db_session.add(run_param)
    await db_session.commit()

    # use new session
    async with session_factory() as separate_session:
        await mark_run_parameter_complete(
            separate_session, RunType.FORECAST, run_datetime, for_date
        )
        await separate_session.commit()

    # verify with a different session
    async with session_factory() as verify_session:
        result = await verify_session.execute(
            select(RunParameters).where(RunParameters.id == run_param.id)
        )
        updated_param = result.scalar_one()
        assert updated_param.complete is True
