"""Integration tests for AdvisoryHFIWindSpeed.min_wind_speed hybrid property.

These tests verify that legacy NaN values stored in the database are normalized
to None when read back through the ORM, without affecting normal values.
"""

from datetime import datetime, timezone

import pytest
from geoalchemy2 import WKTElement
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.future import select
from testcontainers.postgres import PostgresContainer

from wps_shared.db.models import Base
from wps_shared.db.models.auto_spatial_advisory import (
    AdvisoryHFIWindSpeed,
    HfiClassificationThreshold,
    RunParameters,
    Shape,
    ShapeType,
    ShapeTypeEnum,
)
from wps_shared.db.models.psu import FireCentre
from wps_shared.run_type import RunType
from wps_shared.tests.common import TESTCONTAINERS_POSTGRES_IMAGE

test_run_datetime = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
test_for_date = test_run_datetime.date()


@pytest.fixture(scope="function")
def postgres_container():
    with PostgresContainer(TESTCONTAINERS_POSTGRES_IMAGE) as postgres:
        yield postgres


@pytest.fixture(scope="function")
async def engine(postgres_container):
    sync_url = postgres_container.get_connection_url()
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
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'runtypeenum') THEN
                    CREATE TYPE runtypeenum AS ENUM ('actual', 'forecast');
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


@pytest.fixture
async def async_session(session_factory):
    async with session_factory() as session:
        yield session


@pytest.fixture(scope="function")
async def prerequisites(session_factory):
    """Shared prerequisite rows needed for AdvisoryHFIWindSpeed FK constraints."""
    async with session_factory() as session:
        shape_type = ShapeType(name=ShapeTypeEnum.fire_zone_unit)
        fire_centre = FireCentre(name="Test Centre")
        session.add_all([shape_type, fire_centre])
        await session.commit()

        shape = Shape(
            source_identifier="1",
            placename_label="Zone 1",
            fire_centre=fire_centre.id,
            shape_type=shape_type.id,
            geom=WKTElement("MULTIPOLYGON(((0 0, 1 0, 1 1, 0 1, 0 0)))", srid=3005),
        )
        threshold = HfiClassificationThreshold(description="advisory", name="advisory")
        run_param = RunParameters(
            run_type=RunType.FORECAST.value,
            run_datetime=test_run_datetime,
            for_date=test_for_date,
            complete=True,
        )
        session.add_all([shape, threshold, run_param])
        await session.commit()

        return shape, threshold, run_param


@pytest.mark.anyio
async def test_nan_wind_speed_stored_in_db_reads_as_none(async_session, prerequisites):
    """Legacy rows with NaN stored in the DB should surface as None via the hybrid property."""
    shape, threshold, run_param = prerequisites

    await async_session.execute(
        text(
            "INSERT INTO advisory_hfi_wind_speed "
            "(advisory_shape_id, threshold, run_parameters, min_wind_speed) "
            "VALUES (:shape_id, :threshold_id, :run_param_id, 'NaN'::float)"
        ),
        {"shape_id": shape.id, "threshold_id": threshold.id, "run_param_id": run_param.id},
    )
    await async_session.commit()

    # PostgreSQL treats NaN = NaN as true (unlike IEEE 754), so this finds the row.
    result = await async_session.execute(
        text(
            "SELECT id FROM advisory_hfi_wind_speed "
            "WHERE advisory_shape_id = :shape_id AND min_wind_speed = 'NaN'::float "
            "ORDER BY id DESC LIMIT 1"
        ),
        {"shape_id": shape.id},
    )
    row_id = result.scalar_one()

    result = await async_session.execute(
        select(AdvisoryHFIWindSpeed).where(AdvisoryHFIWindSpeed.id == row_id)
    )
    row = result.scalar_one()

    assert row is not None
    assert row.min_wind_speed is None


@pytest.mark.anyio
async def test_finite_wind_speed_passes_through(async_session, prerequisites):
    """Finite values should be returned unchanged."""
    shape, threshold, run_param = prerequisites

    record = AdvisoryHFIWindSpeed(
        advisory_shape_id=shape.id,
        threshold=threshold.id,
        run_parameters=run_param.id,
        min_wind_speed=12.5,
    )
    async_session.add(record)
    await async_session.commit()

    result = await async_session.execute(
        select(AdvisoryHFIWindSpeed).where(AdvisoryHFIWindSpeed.id == record.id)
    )
    fetched = result.scalar_one()

    assert fetched.min_wind_speed == 12.5


@pytest.mark.anyio
async def test_null_wind_speed_passes_through(async_session, prerequisites):
    """NULL values (no data for that zone/threshold) should remain None."""
    shape, threshold, run_param = prerequisites

    record = AdvisoryHFIWindSpeed(
        advisory_shape_id=shape.id,
        threshold=threshold.id,
        run_parameters=run_param.id,
        min_wind_speed=None,
    )
    async_session.add(record)
    await async_session.commit()

    result = await async_session.execute(
        select(AdvisoryHFIWindSpeed).where(AdvisoryHFIWindSpeed.id == record.id)
    )
    fetched = result.scalar_one()

    assert fetched.min_wind_speed is None
