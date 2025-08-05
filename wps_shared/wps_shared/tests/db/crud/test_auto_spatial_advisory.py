import pytest
from datetime import datetime, timezone
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from testcontainers.postgres import PostgresContainer
from sqlalchemy.future import select

from wps_shared.db.models.auto_spatial_advisory import (
    Base,
    HfiClassificationThreshold,
    RunParameters,
    HighHfiArea,
    AdvisoryFuelStats,
    AdvisoryTPIStats,
    AdvisoryHFIWindSpeed,
    AdvisoryHFIPercentConifer,
    CriticalHours,
    Shape,
    ShapeType,
    ShapeTypeEnum,
    FuelType,
    FuelTypeRaster,
    SFMSFuelType,
)
from wps_shared.db.crud.auto_spatial_advisory import check_and_mark_sfms_run_processing_complete
from wps_shared.run_type import RunType


@pytest.fixture(scope="module")
def postgres_container():
    with PostgresContainer("postgis/postgis:15-3.3") as postgres:
        yield postgres


@pytest.fixture
async def db_session(postgres_container):
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

    Session = async_sessionmaker(engine, expire_on_commit=False)

    async with Session() as session:
        yield session

    await engine.dispose()


@pytest.mark.anyio
async def test_check_and_mark_sfms_run_processing_complete(db_session):
    run_datetime = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    for_date = run_datetime.date()

    # Create required base rows
    run_param = RunParameters(
        run_type=RunType.FORECAST.value,
        run_datetime=run_datetime,
        for_date=for_date,
        complete=False,
    )
    shape_type = ShapeType(id=1, name=ShapeTypeEnum.fire_zone_unit)
    threshold = HfiClassificationThreshold(description="advisory threshold", name="advisory")
    raster = FuelTypeRaster(
        id=1,
        year=2025,
        version=1,
        xsize=100,
        ysize=100,
        object_store_path="test/path/to/raster.tif",
        content_hash="abc123",
        create_timestamp=run_datetime,
    )
    sfms_fuel = SFMSFuelType(
        id=1, fuel_type_id=1, fuel_type_code="C1", description="Test SFMS fuel type"
    )
    db_session.add_all([run_param, shape_type, threshold, raster, sfms_fuel])
    await db_session.flush()

    # Shape and HFI Area
    shape = Shape(
        source_identifier="zone-1",
        shape_type=shape_type.id,
        geom="MULTIPOLYGON(((0 0,1 0,1 1,0 1,0 0)))",
    )
    db_session.add(shape)
    await db_session.flush()

    hfi_area = HighHfiArea(
        advisory_shape_id=shape.id,
        threshold=threshold.id,
        run_parameters=run_param.id,
        area=1.0,
    )
    db_session.add(hfi_area)
    await db_session.flush()

    # Fuel Type
    fuel_type = FuelType(
        id=1,
        fuel_type_id=1,
        geom="POLYGON((0 0,1 0,1 1,0 1,0 0))",
        fuel_type_raster_id=raster.id,
    )
    db_session.add(fuel_type)
    await db_session.flush()

    # All Advisory Rows
    db_session.add_all(
        [
            AdvisoryFuelStats(
                run_parameters=run_param.id,
                advisory_shape_id=hfi_area.id,
                threshold=threshold.id,
                fuel_type=fuel_type.id,
                area=1.0,
                fuel_type_raster_id=raster.id,
            ),
            AdvisoryTPIStats(
                run_parameters=run_param.id,
                advisory_shape_id=hfi_area.id,
                valley_bottom=10,
                mid_slope=20,
                upper_slope=30,
                pixel_size_metres=100,
            ),
            AdvisoryHFIWindSpeed(
                run_parameters=run_param.id,
                advisory_shape_id=hfi_area.id,
                threshold=threshold.id,
                min_wind_speed=5.0,
            ),
            AdvisoryHFIPercentConifer(
                run_parameters=run_param.id,
                advisory_shape_id=hfi_area.id,
                fuel_type=fuel_type.id,
                min_percent_conifer=50,
                fuel_type_raster_id=raster.id,
            ),
            CriticalHours(
                run_parameters=run_param.id,
                advisory_shape_id=hfi_area.id,
                threshold=threshold.name,
                fuel_type=fuel_type.id,
                start_hour=10,
                end_hour=18,
                fuel_type_raster_id=raster.id,
            ),
        ]
    )

    await db_session.commit()

    # Run function under test
    await check_and_mark_sfms_run_processing_complete(
        db_session, RunType.FORECAST, run_datetime, for_date
    )

    # Assert it was marked complete
    result = await db_session.execute(select(RunParameters).where(RunParameters.id == run_param.id))
    updated_param = result.scalar_one()
    assert updated_param.complete is True
