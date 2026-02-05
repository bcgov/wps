from datetime import date, datetime, timezone

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.future import select
from testcontainers.postgres import PostgresContainer

from wps_shared.db.crud.sfms_run import save_sfms_run_log, track_sfms_run, update_sfms_run_log
from wps_shared.db.models.sfms_run import (
    SFMSRunLog,
    SFMSRunLogJobName,
    SFMSRunLogStatus,
    SFMSStations,
)


test_target_date = date(2025, 7, 15)
test_started_at = datetime(2025, 7, 15, 20, 30, 0, tzinfo=timezone.utc)
test_completed_at = datetime(2025, 7, 15, 20, 45, 0, tzinfo=timezone.utc)


@pytest.fixture(scope="function")
def postgres_container():
    with PostgresContainer("postgres:16") as postgres:
        yield postgres


@pytest.fixture(scope="function")
async def engine(postgres_container):
    sync_url = postgres_container.get_connection_url()
    db_url = sync_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://")

    engine = create_async_engine(db_url, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(SFMSStations.__table__.create)
        # Insert a mock sfms_stations record
        await conn.execute(
            text("""INSERT INTO sfms_stations (run_type, target_date, run_date, stations)
                 VALUES ('actual', '2026-02-01', '2026-02-02 16:32:15.294322-08', ARRAY[1, 2, 3]);""")
        )
        await conn.run_sync(SFMSRunLog.__table__.create)

    yield engine

    await engine.dispose()


@pytest.fixture(scope="function")
async def session_factory(engine):
    return async_sessionmaker(engine, expire_on_commit=False)


@pytest.fixture(scope="function")
async def async_session(session_factory):
    async with session_factory() as session:
        yield session


@pytest.mark.anyio
async def test_save_sfms_run_log(async_session: AsyncSession):
    """Test inserting a new run log record and getting back its id."""
    log_id = await save_sfms_run_log(
        async_session,
        SFMSRunLogJobName.TEMPERATURE_INTERPOLATION,
        test_started_at,
        SFMSRunLogStatus.RUNNING,
        1,
    )
    await async_session.commit()

    assert log_id is not None
    assert isinstance(log_id, int)

    result = await async_session.execute(select(SFMSRunLog).where(SFMSRunLog.id == log_id))
    saved = result.scalar_one()
    assert saved.job_name == SFMSRunLogJobName.TEMPERATURE_INTERPOLATION
    assert saved.target_date == test_target_date
    assert saved.started_at == test_started_at
    assert saved.status == SFMSRunLogStatus.RUNNING
    assert saved.completed_at is None
    assert saved.sfms_stations_id == 1


@pytest.mark.anyio
async def test_update_sfms_run_log_success(async_session: AsyncSession):
    """Test updating a run log to success status with completed_at."""
    log_id = await save_sfms_run_log(
        async_session,
        SFMSRunLogJobName.TEMPERATURE_INTERPOLATION,
        test_started_at,
        SFMSRunLogStatus.RUNNING,
        1,
    )
    await async_session.commit()

    await update_sfms_run_log(
        async_session, log_id, status=SFMSRunLogStatus.SUCCESS, completed_at=test_completed_at
    )
    await async_session.commit()

    result = await async_session.execute(select(SFMSRunLog).where(SFMSRunLog.id == log_id))
    updated = result.scalar_one()
    assert updated.status == SFMSRunLogStatus.SUCCESS
    assert updated.completed_at == test_completed_at


@pytest.mark.anyio
async def test_update_sfms_run_log_failed(async_session: AsyncSession):
    """Test updating a run log to failed status."""
    log_id = await save_sfms_run_log(
        async_session,
        SFMSRunLogJobName.TEMPERATURE_INTERPOLATION,
        test_started_at,
        SFMSRunLogStatus.RUNNING,
        1,
    )
    await async_session.commit()

    await update_sfms_run_log(
        async_session, log_id, status=SFMSRunLogStatus.FAILED, completed_at=test_completed_at
    )
    await async_session.commit()

    result = await async_session.execute(select(SFMSRunLog).where(SFMSRunLog.id == log_id))
    updated = result.scalar_one()
    assert updated.status == SFMSRunLogStatus.FAILED
    assert updated.completed_at == test_completed_at


@pytest.mark.anyio
async def test_multiple_run_logs(async_session: AsyncSession):
    """Test inserting multiple run log records for different jobs returns unique ids."""
    record1 = await save_sfms_run_log(
        async_session,
        SFMSRunLogJobName.TEMPERATURE_INTERPOLATION,
        test_started_at,
        SFMSRunLogStatus.RUNNING,
        1,
    )
    record2 = await save_sfms_run_log(
        async_session,
        SFMSRunLogJobName.PRECIPITATION_INTERPOLATION,
        datetime(2025, 7, 15, 20, 35, 0, tzinfo=timezone.utc),
        SFMSRunLogStatus.RUNNING,
        1,
    )

    id1 = await save_sfms_run_log(async_session, record1)
    id2 = await save_sfms_run_log(async_session, record2)
    await async_session.commit()

    assert id1 != id2

    result = await async_session.execute(select(SFMSRunLog))
    rows = result.scalars().all()
    assert len(rows) == 2
    job_names = {r.job_name for r in rows}
    assert job_names == {
        SFMSRunLogJobName.TEMPERATURE_INTERPOLATION,
        SFMSRunLogJobName.PRECIPITATION_INTERPOLATION,
    }


@pytest.mark.anyio
async def test_track_sfms_run_success(async_session: AsyncSession):
    """Test decorator records success when the wrapped function succeeds."""
    target = datetime(2025, 7, 15, 0, 0, 0, tzinfo=timezone.utc)
    called = False

    @track_sfms_run(SFMSRunLogJobName.TEMPERATURE_INTERPOLATION, target, 1, async_session)
    async def my_job() -> None:
        nonlocal called
        called = True

    await my_job()

    assert called

    result = await async_session.execute(select(SFMSRunLog))
    row = result.scalar_one()
    assert row.job_name == SFMSRunLogJobName.TEMPERATURE_INTERPOLATION
    assert row.target_date == target.date()
    assert row.status == SFMSRunLogStatus.SUCCESS
    assert row.started_at is not None
    assert row.completed_at is not None
    assert row.completed_at >= row.started_at


@pytest.mark.anyio
async def test_track_sfms_run_failure(async_session: AsyncSession):
    """Test decorator records failure and re-raises when the wrapped function raises."""
    target = datetime(2025, 7, 15, 0, 0, 0, tzinfo=timezone.utc)

    @track_sfms_run(SFMSRunLogJobName.PRECIPITATION_INTERPOLATION, target, 1, async_session)
    async def my_failing_job() -> None:
        raise RuntimeError("something went wrong")

    with pytest.raises(RuntimeError, match="something went wrong"):
        await my_failing_job()

    result = await async_session.execute(select(SFMSRunLog))
    row = result.scalar_one()
    assert row.job_name == SFMSRunLogJobName.PRECIPITATION_INTERPOLATION
    assert row.status == SFMSRunLogStatus.FAILED
    assert row.completed_at is not None


@pytest.mark.anyio
async def test_track_sfms_run_preserves_return_value(async_session: AsyncSession):
    """Test decorator passes through the return value of the wrapped function."""
    target = datetime(2025, 7, 15, 0, 0, 0, tzinfo=timezone.utc)

    @track_sfms_run(SFMSRunLogJobName.TEMPERATURE_INTERPOLATION, target, 1, async_session)
    async def my_job() -> str:
        return "result"

    result = await my_job()
    assert result == "result"


@pytest.mark.anyio
async def test_track_sfms_run_preserves_function_name(async_session: AsyncSession):
    """Test decorator preserves the wrapped function's name via functools.wraps."""
    target = datetime(2025, 7, 15, 0, 0, 0, tzinfo=timezone.utc)

    @track_sfms_run(SFMSRunLogJobName.TEMPERATURE_INTERPOLATION, target, 1, async_session)
    async def original_name() -> None:
        pass

    assert original_name.__name__ == "original_name"
