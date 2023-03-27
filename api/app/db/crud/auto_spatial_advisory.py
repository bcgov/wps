from datetime import date, datetime
from enum import Enum
import logging
from time import perf_counter
from typing import List
from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.engine.row import Row
from app.auto_spatial_advisory.run_type import RunType
from app.db.models.auto_spatial_advisory import (
    Shape, ClassifiedHfi, HfiClassificationThreshold, SFMSFuelType, RunTypeEnum,
    FuelType, HighHfiArea, RunParameters, AdvisoryElevationStats)

logger = logging.getLogger(__name__)


class HfiClassificationThresholdEnum(Enum):
    """ Enum for the different HFI classification thresholds. """
    ADVISORY = 'advisory'
    WARNING = 'warning'


async def get_hfi_classification_threshold(session: AsyncSession,
                                           name: HfiClassificationThresholdEnum) -> HfiClassificationThreshold:
    stmt = select(HfiClassificationThreshold).where(
        HfiClassificationThreshold.name == name.value)
    result = await session.execute(stmt)
    return result.scalars().first()


async def save_hfi(session: AsyncSession, hfi: ClassifiedHfi):
    session.add(hfi)


async def save_fuel_type(session: AsyncSession, fuel_type: FuelType):
    session.add(fuel_type)


async def get_hfi(session: AsyncSession, run_type: RunTypeEnum, run_date: datetime, for_date: date):
    stmt = select(ClassifiedHfi).where(
        ClassifiedHfi.run_type == run_type,
        ClassifiedHfi.for_date == for_date,
        ClassifiedHfi.run_datetime == run_date)
    result = await session.execute(stmt)
    return result.scalars()


async def get_combustible_area(session: AsyncSession):
    """ Get the combustible area for each "shape". This is slow, and we don't expect it to run
    in real time.

    This method isn't being used right now, but you can calculate the combustible area for each
    zone as follows:

    ```python
    from app.db.crud.auto_spatial_advisory import get_combustible_area
    from app.db.database import get_async_read_session_scope

    async with get_async_read_session_scope() as session:
    result = await get_combustible_area(session)

    for record in result:
        print(record)
        print(record['combustible_area']/record['zone_area'])
    ```

    """
    logger.info('starting zone/combustible area intersection query')
    perf_start = perf_counter()
    stmt = select(Shape.id,
                  Shape.source_identifier,
                  Shape.geom.ST_Area().label('zone_area'),
                  FuelType.geom.ST_Union().ST_Intersection(Shape.geom).ST_Area().label('combustible_area'))\
        .join(FuelType, FuelType.geom.ST_Intersects(Shape.geom))\
        .where(FuelType.fuel_type_id.not_in((-10000, 99, 100, 102, 103)))\
        .group_by(Shape.id)
    result = await session.execute(stmt)
    all_combustible = result.all()
    perf_end = perf_counter()
    delta = perf_end - perf_start
    logger.info('%f delta count before and after hfi area + zone/area intersection query', delta)
    return all_combustible


async def get_all_hfi_thresholds(session: AsyncSession) -> List[HfiClassificationThreshold]:
    """
    Retrieve all records from advisory_hfi_classification_threshold table.
    """
    logger.info('retrieving HFI classification threshold info...')
    stmt = select(HfiClassificationThreshold)
    result = await session.execute(stmt)

    thresholds = []

    for row in result.all():
        threshold_object = row[0]
        thresholds.append(HfiClassificationThreshold(id=threshold_object.id,
                                                     description=threshold_object.description,
                                                     name=threshold_object.name))

    return thresholds


async def get_all_sfms_fuel_types(session: AsyncSession) -> List[SFMSFuelType]:
    """
    Retrieve all records from sfms_fuel_types table
    """
    logger.info('retrieving SFMS fuel types info...')
    stmt = select(SFMSFuelType)
    result = await session.execute(stmt)

    fuel_types = []

    for row in result.all():
        fuel_type_object = row[0]
        fuel_types.append(SFMSFuelType(fuel_type_id=fuel_type_object.fuel_type_id,
                                       fuel_type_code=fuel_type_object.fuel_type_code,
                                       description=fuel_type_object.description))

    return fuel_types


async def get_high_hfi_fuel_types_for_zone(session: AsyncSession,
                                           run_type: RunTypeEnum,
                                           run_datetime: datetime,
                                           for_date: date,
                                           zone_id: int) -> List[Row]:
    """
    Union of fuel types by fuel_type_id (1 multipolygon for each fuel type)
    Intersected with union of ClassifiedHfi for given run_type, run_datetime, and for_date
        for both 4K-10K and 10K+ HFI values
    Intersected with fire zone geom for a specific fire zone identified by ID
    """
    logger.info('starting fuel types/high hfi/zone intersection query for fire zone %s', str(zone_id))
    perf_start = perf_counter()

    stmt = select(Shape.source_identifier, FuelType.fuel_type_id, ClassifiedHfi.threshold,
                  func.sum(FuelType.geom.ST_Intersection(ClassifiedHfi.geom.ST_Intersection(Shape.geom)).ST_Area()).label('area'))\
        .join_from(ClassifiedHfi, Shape, ClassifiedHfi.geom.ST_Intersects(Shape.geom))\
        .join_from(ClassifiedHfi, FuelType, ClassifiedHfi.geom.ST_Intersects(FuelType.geom))\
        .where(ClassifiedHfi.run_type == run_type.value, ClassifiedHfi.for_date == for_date,
               ClassifiedHfi.run_datetime == run_datetime, Shape.source_identifier == str(zone_id))\
        .group_by(Shape.source_identifier)\
        .group_by(FuelType.fuel_type_id)\
        .group_by(ClassifiedHfi.threshold)\
        .order_by(FuelType.fuel_type_id)\
        .order_by(ClassifiedHfi.threshold)

    result = await session.execute(stmt)
    perf_end = perf_counter()
    delta = perf_end - perf_start
    logger.info('%f delta count before and after fuel types/high hfi/zone intersection query', delta)
    return result.all()


async def get_fuel_types_with_high_hfi(session: AsyncSession,
                                       run_type: RunTypeEnum,
                                       run_datetime: datetime,
                                       for_date: date) -> List[Row]:
    """
    Union of fuel types by fuel_type_id (1 multipolygon for each type of fuel)
    Intersect with union of ClassifiedHfi for given run_type, run_datetime, and for_date
        for both 4K-10K and 10K+ HFI values
    Intersection with fire zone geom
    """
    logger.info('starting fuel types/high hfi/zone intersection query')
    perf_start = perf_counter()

    stmt = select(Shape.source_identifier, FuelType.fuel_type_id, ClassifiedHfi.threshold,
                  func.sum(FuelType.geom.ST_Intersection(ClassifiedHfi.geom.ST_Intersection(Shape.geom)).ST_Area()).label('area'))\
        .join_from(ClassifiedHfi, Shape, ClassifiedHfi.geom.ST_Intersects(Shape.geom))\
        .join_from(ClassifiedHfi, FuelType, ClassifiedHfi.geom.ST_Intersects(FuelType.geom))\
        .where(ClassifiedHfi.run_type == run_type.value, ClassifiedHfi.for_date == for_date, ClassifiedHfi.run_datetime == run_datetime)\
        .group_by(Shape.source_identifier)\
        .group_by(FuelType.fuel_type_id)\
        .group_by(ClassifiedHfi.threshold)\
        .order_by(Shape.source_identifier)\
        .order_by(FuelType.fuel_type_id)\
        .order_by(ClassifiedHfi.threshold)

    result = await session.execute(stmt)

    perf_end = perf_counter()
    delta = perf_end - perf_start
    logger.info('%f delta count before and after fuel types/high hfi/zone intersection query', delta)
    return result.all()


async def get_hfi_area(session: AsyncSession,
                       run_type: RunTypeEnum,
                       run_datetime: datetime,
                       for_date: date) -> List[Row]:
    logger.info('gathering hfi area data')
    stmt = select(Shape.id, Shape.source_identifier, Shape.combustible_area, HighHfiArea.id,
                  HighHfiArea.advisory_shape_id, HighHfiArea.threshold, HighHfiArea.area.label('hfi_area'))\
        .join(HighHfiArea, HighHfiArea.advisory_shape_id == Shape.id)\
        .join(RunParameters, RunParameters.id == HighHfiArea.run_parameters)\
        .where(RunParameters.run_type == run_type.value,
               RunParameters.for_date == for_date,
               RunParameters.run_datetime == run_datetime)
    result = await session.execute(stmt)
    return result.all()


async def get_run_datetimes(session: AsyncSession, run_type: RunTypeEnum, for_date: date) -> List[Row]:
    """
    Retrieve all distinct available run_datetimes for a given run_type and for_date, and return the run_datetimes
    in descending order (most recent is first)
    """
    stmt = select(ClassifiedHfi.run_datetime)\
        .where(ClassifiedHfi.run_type == run_type.value, ClassifiedHfi.for_date == for_date)\
        .distinct()\
        .order_by(ClassifiedHfi.run_datetime.desc())
    result = await session.execute(stmt)
    return result.all()


async def get_high_hfi_area(session: AsyncSession,
                            run_type: RunTypeEnum,
                            run_datetime: datetime,
                            for_date: date) -> List[Row]:
    """ For each fire zone, get the area of HFI polygons in that zone that fall within the 
    4000 - 10000 range and the area of HFI polygons that exceed the 10000 threshold.
    """
    stmt = select(HighHfiArea.id,
                  HighHfiArea.advisory_shape_id,
                  HighHfiArea.area,
                  HighHfiArea.threshold)\
        .join(RunParameters)\
        .where(RunParameters.run_type == run_type.value,
               RunParameters.for_date == for_date,
               RunParameters.run_datetime == run_datetime)
    result = await session.execute(stmt)
    return result.all()


async def save_high_hfi_area(session: AsyncSession, high_hfi_area: HighHfiArea):
    session.add(high_hfi_area)


async def calculate_high_hfi_areas(session: AsyncSession, run_type: RunType, run_datetime: datetime,
                                   for_date: date) -> List[Row]:
    """
        Given a 'run_parameters_id', which represents a unqiue combination of run_type, run_datetime
        and for_date, individually sum the areas in each firezone with:
            1. 4000 <= HFI < 10000 (aka 'advisory_area')
            2. HFI >= 10000 (aka 'warn_area')
    """
    logger.info('starting high HFI by zone intersection query')
    perf_start = perf_counter()

    stmt = select(Shape.id.label('shape_id'),
                  ClassifiedHfi.threshold.label('threshold'),
                  func.sum(ClassifiedHfi.geom.ST_Intersection(Shape.geom).ST_Area()).label('area'))\
        .join_from(Shape, ClassifiedHfi, ClassifiedHfi.geom.ST_Intersects(Shape.geom))\
        .where(ClassifiedHfi.run_type == run_type.value)\
        .where(ClassifiedHfi.run_datetime == run_datetime)\
        .where(ClassifiedHfi.for_date == for_date)\
        .group_by(Shape.id)\
        .group_by(ClassifiedHfi.threshold)

    result = await session.execute(stmt)
    all_high_hfi = result.all()
    perf_end = perf_counter()
    delta = perf_end - perf_start
    logger.info('%f delta count before and after calculate high HFI by zone intersection query', delta)
    return all_high_hfi


async def get_run_parameters_id(session: AsyncSession,
                                run_type: RunTypeEnum,
                                run_datetime: datetime,
                                for_date: date) -> List[Row]:
    stmt = select(RunParameters.id)\
        .where(RunParameters.run_type == run_type.value,
               RunParameters.run_datetime == run_datetime,
               RunParameters.for_date == for_date)
    result = await session.execute(stmt)
    return result.scalar()


async def save_run_parameters(session: AsyncSession, run_type: RunType, run_datetime: datetime, for_date: date):
    logger.info(
        f'Writing run parameters. RunType: {run_type.value}; run_datetime: {run_datetime.isoformat()}; for_date: {for_date.isoformat()}')
    stmt = insert(RunParameters)\
        .values(run_type=run_type.value, run_datetime=run_datetime, for_date=for_date)\
        .on_conflict_do_nothing()
    await session.execute(stmt)


async def save_advisory_elevation_stats(session: AsyncSession, advisory_elevation_stats: AdvisoryElevationStats):
    session.add(advisory_elevation_stats)


async def get_zonal_elevation_stats(session: AsyncSession,
                                    fire_zone_id: int,
                                    run_type: RunTypeEnum,
                                    run_datetime: datetime,
                                    for_date: date) -> List[Row]:
    run_parameters_id = await get_run_parameters_id(session, run_type, run_datetime, for_date)
    stmt = select(Shape.id).where(Shape.source_identifier == str(fire_zone_id))
    result = await session.execute(stmt)
    shape_id = result.scalar()

    stmt = select(AdvisoryElevationStats.advisory_shape_id, AdvisoryElevationStats.minimum,
                  AdvisoryElevationStats.quartile_25, AdvisoryElevationStats.median, AdvisoryElevationStats.quartile_75,
                  AdvisoryElevationStats.maximum, AdvisoryElevationStats.threshold)\
        .where(AdvisoryElevationStats.advisory_shape_id == shape_id, AdvisoryElevationStats.run_parameters == run_parameters_id)\
        .order_by(AdvisoryElevationStats.threshold)

    return await session.execute(stmt)
