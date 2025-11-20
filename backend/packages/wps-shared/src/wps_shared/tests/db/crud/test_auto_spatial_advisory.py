from datetime import datetime, timezone

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.future import select
from testcontainers.postgres import PostgresContainer

from wps_shared.db.crud.auto_spatial_advisory import mark_run_parameter_complete
from wps_shared.db.models import Base
from wps_shared.db.models.auto_spatial_advisory import RunParameters
from wps_shared.run_type import RunType


@pytest.fixture(scope="function")
def postgres_container():
    with PostgresContainer("postgis/postgis:15-3.3") as postgres:
        yield postgres


@pytest.fixture(scope="function")
async def engine(postgres_container):
    # Get the connection URL from the container (includes correct credentials)
    sync_url = postgres_container.get_connection_url()
    # Convert to asyncpg URL for async operations (psycopg2 -> asyncpg)
    db_url = sync_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://")

    engine = create_async_engine(db_url, echo=False)

    async with engine.begin() as conn:
        await conn.execute(
            text("""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'hficlassificationthresholdenum') THEN
                    CREATE TYPE hficlassificationthresholdenum AS ENUM ('advisory', 'warning');
                END IF;
            END
            $$;
        """)
        )
        await conn.run_sync(Base.metadata.create_all)

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
async def test_mark_run_parameter_complete(async_session, session_factory):
    run_datetime = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    for_date = run_datetime.date()

    run_param = RunParameters(
        run_type=RunType.FORECAST.value,
        run_datetime=run_datetime,
        for_date=for_date,
        complete=False,
    )
    async_session.add(run_param)
    await async_session.commit()

    result = await async_session.execute(
        select(RunParameters).where(RunParameters.id == run_param.id)
    )
    fetched_param = result.scalar_one()
    assert fetched_param.complete is False

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
