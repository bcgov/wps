from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from testcontainers.postgres import PostgresContainer
from wps_shared.db.models import Base
import pytest


@pytest.fixture(scope="function")
def postgres_container():
    with PostgresContainer("postgis/postgis:15-3.3") as postgres:
        yield postgres


@pytest.fixture(scope="function")
async def engine(postgres_container):
    host = postgres_container.get_container_host_ip()
    port = postgres_container.get_exposed_port(5432)
    db_url = f"postgresql+asyncpg://test:test@{host}:{port}/test"

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
def session_factory(engine):
    return async_sessionmaker(engine, expire_on_commit=False)


@pytest.fixture(scope="function")
async def db_session(session_factory):
    async with session_factory() as session:
        yield session
