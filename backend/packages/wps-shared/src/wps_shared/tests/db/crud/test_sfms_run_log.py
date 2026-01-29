from datetime import date, datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.future import select
from testcontainers.postgres import PostgresContainer

from wps_shared.db.crud.sfms_run_log import save_sfms_run_log, update_sfms_run_log
from wps_shared.db.models.sfms_run_log import SFMSRunLog


test_target_date = date(2025, 7, 15)
test_started_at = datetime(2025, 7, 15, 20, 30, 0, tzinfo=timezone.utc)
test_completed_at = datetime(2025, 7, 15, 20, 45, 0, tzinfo=timezone.utc)


@pytest.fixture(scope="function")
def postgres_container():
    with PostgresContainer("postgis/postgis:15-3.3") as postgres:
        yield postgres


@pytest.fixture(scope="function")
async def engine(postgres_container):
    sync_url = postgres_container.get_connection_url()
    db_url = sync_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://")

    engine = create_async_engine(db_url, echo=False)

    async with engine.begin() as conn:
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
async def test_save_sfms_run_log(async_session):
    """Test inserting a new run log record and getting back its id."""
    record = SFMSRunLog(
        job_name="temperature_interpolation",
        target_date=test_target_date,
        started_at=test_started_at,
        status="running",
    )
    log_id = await save_sfms_run_log(async_session, record)
    await async_session.commit()

    assert log_id is not None
    assert isinstance(log_id, int)

    result = await async_session.execute(select(SFMSRunLog).where(SFMSRunLog.id == log_id))
    saved = result.scalar_one()
    assert saved.job_name == "temperature_interpolation"
    assert saved.target_date == test_target_date
    assert saved.started_at == test_started_at
    assert saved.status == "running"
    assert saved.completed_at is None


@pytest.mark.anyio
async def test_update_sfms_run_log_success(async_session):
    """Test updating a run log to success status with completed_at."""
    record = SFMSRunLog(
        job_name="precipitation_interpolation",
        target_date=test_target_date,
        started_at=test_started_at,
        status="running",
    )
    log_id = await save_sfms_run_log(async_session, record)
    await async_session.commit()

    await update_sfms_run_log(async_session, log_id, status="success", completed_at=test_completed_at)
    await async_session.commit()

    result = await async_session.execute(select(SFMSRunLog).where(SFMSRunLog.id == log_id))
    updated = result.scalar_one()
    assert updated.status == "success"
    assert updated.completed_at == test_completed_at


@pytest.mark.anyio
async def test_update_sfms_run_log_failed(async_session):
    """Test updating a run log to failed status."""
    record = SFMSRunLog(
        job_name="temperature_interpolation",
        target_date=test_target_date,
        started_at=test_started_at,
        status="running",
    )
    log_id = await save_sfms_run_log(async_session, record)
    await async_session.commit()

    await update_sfms_run_log(async_session, log_id, status="failed", completed_at=test_completed_at)
    await async_session.commit()

    result = await async_session.execute(select(SFMSRunLog).where(SFMSRunLog.id == log_id))
    updated = result.scalar_one()
    assert updated.status == "failed"
    assert updated.completed_at == test_completed_at


@pytest.mark.anyio
async def test_multiple_run_logs(async_session):
    """Test inserting multiple run log records for different jobs returns unique ids."""
    record1 = SFMSRunLog(
        job_name="temperature_interpolation",
        target_date=test_target_date,
        started_at=test_started_at,
        status="running",
    )
    record2 = SFMSRunLog(
        job_name="precipitation_interpolation",
        target_date=test_target_date,
        started_at=datetime(2025, 7, 15, 20, 35, 0, tzinfo=timezone.utc),
        status="running",
    )

    id1 = await save_sfms_run_log(async_session, record1)
    id2 = await save_sfms_run_log(async_session, record2)
    await async_session.commit()

    assert id1 != id2

    result = await async_session.execute(select(SFMSRunLog))
    rows = result.scalars().all()
    assert len(rows) == 2
    job_names = {r.job_name for r in rows}
    assert job_names == {"temperature_interpolation", "precipitation_interpolation"}
