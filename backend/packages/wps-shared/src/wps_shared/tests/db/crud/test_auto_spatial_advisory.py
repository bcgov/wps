from datetime import datetime, timezone

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.future import select
from testcontainers.postgres import PostgresContainer

from wps_shared.db.crud.auto_spatial_advisory import (
    mark_run_parameter_complete,
    get_provincial_rollup,
)
from wps_shared.db.models import Base
from wps_shared.db.models.auto_spatial_advisory import RunParameters
from wps_shared.run_type import RunType
from wps_shared.db.models.auto_spatial_advisory import (
    Shape,
    AdvisoryZoneStatus,
    ShapeType,
    ShapeTypeEnum,
)
from wps_shared.db.models.fuel_type_raster import FuelTypeRaster
from wps_shared.db.models.hfi_calc import FireCentre
from geoalchemy2 import WKTElement

test_run_datetime = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
test_for_date = test_run_datetime.date()


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
    run_param = RunParameters(
        run_type=RunType.FORECAST.value,
        run_datetime=test_run_datetime,
        for_date=test_for_date,
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
            separate_session, RunType.FORECAST, test_run_datetime, test_for_date
        )
        await separate_session.commit()

    # verify with a different session
    async with session_factory() as verify_session:
        result = await verify_session.execute(
            select(RunParameters).where(RunParameters.id == run_param.id)
        )
        updated_param = result.scalar_one()
        assert updated_param.complete is True


@pytest.mark.anyio
async def test_get_provincial_rollup(async_session):
    # Create RunParameters
    run_param = RunParameters(
        run_type=RunType.FORECAST.value,
        run_datetime=test_run_datetime,
        for_date=test_for_date,
        complete=True,
    )
    async_session.add(run_param)
    await async_session.commit()

    # Create ShapeType
    shape_type = ShapeType(name=ShapeTypeEnum.fire_zone_unit)
    async_session.add(shape_type)
    await async_session.commit()

    # Create FuelTypeRaster
    fuel_raster = FuelTypeRaster(
        year=2023,
        version=1,
        xsize=100,
        ysize=100,
        object_store_path="dummy",
        content_hash="dummy",
        create_timestamp=datetime.now(timezone.utc),
    )
    async_session.add(fuel_raster)
    await async_session.commit()

    # Create FireCentre
    fire_centre = FireCentre(name="Test Centre")
    async_session.add(fire_centre)
    await async_session.commit()

    # Create Shapes
    shape1 = Shape(
        source_identifier="1",
        placename_label="Zone 1",
        fire_centre=fire_centre.id,
        shape_type=shape_type.id,
        geom=WKTElement("MULTIPOLYGON(((0 0, 1 0, 1 1, 0 1, 0 0)))", srid=3005),
    )
    shape2 = Shape(
        source_identifier="2",
        placename_label="Zone 2",
        fire_centre=fire_centre.id,
        shape_type=shape_type.id,
        geom=WKTElement("MULTIPOLYGON(((0 0, 1 0, 1 1, 0 1, 0 0)))", srid=3005),
    )
    async_session.add_all([shape1, shape2])
    await async_session.commit()

    # shape1: warning_percentage > 20 -> WARNING
    status1 = AdvisoryZoneStatus(
        advisory_shape_id=shape1.id,
        run_parameters=run_param.id,
        fuel_type_raster_id=fuel_raster.id,
        advisory_percentage=10.0,
        warning_percentage=25.0,
    )
    # shape2: advisory + warning > 20 -> ADVISORY
    status2 = AdvisoryZoneStatus(
        advisory_shape_id=shape2.id,
        run_parameters=run_param.id,
        fuel_type_raster_id=fuel_raster.id,
        advisory_percentage=15.0,
        warning_percentage=10.0,
    )
    async_session.add_all([status1, status2])
    await async_session.commit()

    result = await get_provincial_rollup(
        async_session, RunType.FORECAST, test_run_datetime, test_for_date
    )

    assert len(result) == 2

    result_dict = {r.fire_shape_id: r for r in result}
    assert result_dict[1].status == "warning"
    assert result_dict[2].status == "advisory"
    assert result_dict[1].fire_shape_name == "Zone 1"
    assert result_dict[1].fire_centre_name == "Test Centre"


@pytest.mark.anyio
async def test_get_provincial_rollup_with_multiple_fuel_rasters(async_session):
    run_datetime = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    for_date = run_datetime.date()

    # Create RunParameters
    run_param = RunParameters(
        run_type=RunType.FORECAST.value,
        run_datetime=run_datetime,
        for_date=for_date,
        complete=True,
    )
    async_session.add(run_param)
    await async_session.commit()

    # Create FireCentre
    fire_centre = FireCentre(name="Test Centre")
    async_session.add(fire_centre)
    await async_session.commit()

    # Create ShapeType
    shape_type = ShapeType(name=ShapeTypeEnum.fire_zone_unit)
    async_session.add(shape_type)
    await async_session.commit()

    # Create FuelTypeRasters: 2024 and 2025
    fuel_raster_2024 = FuelTypeRaster(
        year=2024,
        version=1,
        xsize=100,
        ysize=100,
        object_store_path="dummy2024",
        content_hash="dummy2024",
        create_timestamp=datetime.now(timezone.utc),
    )
    fuel_raster_2025 = FuelTypeRaster(
        year=2025,
        version=1,
        xsize=100,
        ysize=100,
        object_store_path="dummy2025",
        content_hash="dummy2025",
        create_timestamp=datetime.now(timezone.utc),
    )
    async_session.add_all([fuel_raster_2024, fuel_raster_2025])
    await async_session.commit()

    # Create Shape
    shape1 = Shape(
        source_identifier="1",
        placename_label="Zone 1",
        fire_centre=fire_centre.id,
        shape_type=shape_type.id,
        geom=WKTElement("MULTIPOLYGON(((0 0, 1 0, 1 1, 0 1, 0 0)))", srid=3005),
    )
    async_session.add_all([shape1])
    await async_session.commit()

    # AdvisoryZoneStatus
    # 2024 raster - no advisory/warning -> NONE
    status1 = AdvisoryZoneStatus(
        advisory_shape_id=shape1.id,
        run_parameters=run_param.id,
        fuel_type_raster_id=fuel_raster_2024.id,
        advisory_percentage=4,
        warning_percentage=1,
    )
    # 2025 raster - warning_percentage > 20 -> WARNING
    status2 = AdvisoryZoneStatus(
        advisory_shape_id=shape1.id,
        run_parameters=run_param.id,
        fuel_type_raster_id=fuel_raster_2025.id,
        advisory_percentage=15,
        warning_percentage=22,
    )
    async_session.add_all([status1, status2])
    await async_session.commit()

    result = await get_provincial_rollup(async_session, RunType.FORECAST, run_datetime, for_date)

    assert len(result) == 1
    assert result[0].status == "warning"
