from datetime import date, datetime, timezone

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from testcontainers.postgres import PostgresContainer

from wps_shared.db.crud.fuel_layer import (
    get_latest_temporal_fuel_raster_version,
    get_matching_temporal_fuel_raster,
    lock_temporal_fuel_raster_date,
)
from wps_shared.db.models.fuel_type_raster import FuelTypeRaster
from wps_shared.db.models.temporal_fuel_raster import TemporalFuelRaster
from wps_shared.tests.common import TESTCONTAINERS_POSTGRES_IMAGE

FOR_DATE = date(2026, 7, 1)
CREATED = datetime(2026, 7, 1, 20, tzinfo=timezone.utc)


@pytest.fixture(scope="module")
def postgres_container():
    with PostgresContainer(TESTCONTAINERS_POSTGRES_IMAGE) as postgres:
        yield postgres


@pytest.fixture
async def engine(postgres_container):
    sync_url = postgres_container.get_connection_url()
    db_url = sync_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://")

    engine = create_async_engine(db_url, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(FuelTypeRaster.__table__.create, checkfirst=True)
        await conn.run_sync(TemporalFuelRaster.__table__.create, checkfirst=True)
        # the container is shared across the module, so start every test from empty tables
        await conn.execute(text("TRUNCATE temporal_fuel_raster, fuel_type_raster"))

    yield engine

    await engine.dispose()


@pytest.fixture
def session_factory(engine):
    return async_sessionmaker(engine, expire_on_commit=False)


@pytest.fixture
async def async_session(session_factory):
    async with session_factory() as session:
        yield session


def fuel_type_raster(id: int) -> FuelTypeRaster:
    return FuelTypeRaster(
        id=id,
        year=2026,
        version=id,
        xsize=778,
        ysize=683,
        object_store_path=f"sfms/static/fuel/2026/fbp2026_v{id}.tif",
        content_hash=f"base-{id}",
        create_timestamp=CREATED,
    )


JULIAN_HASHES = {
    "green_up_on_hash": "on",
    "green_up_off_hash": "off",
    "grass_standing_hash": "standing",
    "grass_matted_hash": "matted",
}


def temporal_fuel_raster(
    for_date: date, version: int, fuel_type_raster_id: int = 1, **julian_hashes: str
) -> TemporalFuelRaster:
    return TemporalFuelRaster(
        fuel_type_raster_id=fuel_type_raster_id,
        for_date=for_date,
        version=version,
        object_store_path=f"temporal/{for_date}/{version}.tif",
        content_hash=f"temporal-{version}",
        green_up_on_archive_path="archive/on.tif",
        green_up_off_archive_path="archive/off.tif",
        grass_standing_archive_path="archive/standing.tif",
        grass_matted_archive_path="archive/matted.tif",
        create_timestamp=CREATED,
        **{**JULIAN_HASHES, **julian_hashes},
    )


@pytest.fixture
async def seeded_session(async_session: AsyncSession):
    async_session.add_all([fuel_type_raster(1), fuel_type_raster(2)])
    await async_session.flush()
    async_session.add_all(
        [
            temporal_fuel_raster(FOR_DATE, 1),
            temporal_fuel_raster(FOR_DATE, 2),
            # same date rebuilt from a different base raster and Julian date rasters
            temporal_fuel_raster(
                FOR_DATE, 3, fuel_type_raster_id=2, green_up_on_hash="on-2", grass_matted_hash="m-2"
            ),
            temporal_fuel_raster(date(2026, 7, 2), 1),
        ]
    )
    await async_session.commit()
    return async_session


@pytest.mark.anyio
async def test_get_temporal_fuel_raster_returns_latest_matching_version(
    seeded_session: AsyncSession,
):
    result = await get_matching_temporal_fuel_raster(seeded_session, FOR_DATE, 1, **JULIAN_HASHES)

    assert result is not None
    assert (result.for_date, result.version) == (FOR_DATE, 2)


@pytest.mark.anyio
@pytest.mark.parametrize(
    "fuel_type_raster_id,changed_hash",
    [
        (2, {}),  # different base raster
        (1, {"green_up_on_hash": "on-2"}),
        (1, {"green_up_off_hash": "off-2"}),
        (1, {"grass_standing_hash": "standing-2"}),
        (1, {"grass_matted_hash": "matted-2"}),
    ],
)
async def test_get_temporal_fuel_raster_requires_all_inputs_to_match(
    seeded_session: AsyncSession, fuel_type_raster_id: int, changed_hash: dict[str, str]
):
    result = await get_matching_temporal_fuel_raster(
        seeded_session, FOR_DATE, fuel_type_raster_id, **{**JULIAN_HASHES, **changed_hash}
    )

    assert result is None


@pytest.mark.anyio
async def test_get_latest_temporal_fuel_raster_version_spans_all_inputs_for_the_date(
    seeded_session: AsyncSession,
):
    assert await get_latest_temporal_fuel_raster_version(seeded_session, FOR_DATE) == 3
    assert await get_latest_temporal_fuel_raster_version(seeded_session, date(2026, 7, 2)) == 1


@pytest.mark.anyio
async def test_get_latest_temporal_fuel_raster_version_is_zero_without_rasters(
    seeded_session: AsyncSession,
):
    assert await get_latest_temporal_fuel_raster_version(seeded_session, date(2026, 7, 3)) == 0


async def lock_without_waiting(session: AsyncSession, for_date: date) -> None:
    """Take the date lock, failing immediately instead of waiting if another session holds it."""
    await session.execute(text("SET LOCAL lock_timeout = '1ms'"))
    await lock_temporal_fuel_raster_date(session, for_date)


@pytest.mark.anyio
async def test_lock_temporal_fuel_raster_date_blocks_same_date_until_commit(session_factory):
    async with session_factory() as holder, session_factory() as waiter:
        await lock_temporal_fuel_raster_date(holder, FOR_DATE)

        # a different date is not blocked
        await lock_without_waiting(waiter, date(2026, 7, 2))
        await waiter.commit()

        with pytest.raises(DBAPIError, match="lock timeout"):
            await lock_without_waiting(waiter, FOR_DATE)
        await waiter.rollback()

        await holder.commit()
        await lock_without_waiting(waiter, FOR_DATE)
        await waiter.commit()
