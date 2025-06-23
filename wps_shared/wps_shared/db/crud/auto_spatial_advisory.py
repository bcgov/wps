import logging
from collections import defaultdict
from datetime import date, datetime
from enum import Enum
from time import perf_counter
from typing import List, Optional, Tuple

from sqlalchemy import String, and_, cast, extract, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine.row import Row
from sqlalchemy.ext.asyncio import AsyncSession

from wps_shared.db.models.auto_spatial_advisory import (
    AdvisoryElevationStats,
    AdvisoryFuelStats,
    AdvisoryHFIPercentConifer,
    AdvisoryHFIWindSpeed,
    AdvisoryShapeFuels,
    AdvisoryTPIStats,
    ClassifiedHfi,
    CombustibleArea,
    CriticalHours,
    FuelType,
    HfiClassificationThreshold,
    HfiClassificationThresholdEnum,
    HighHfiArea,
    RunParameters,
    RunTypeEnum,
    SFMSFuelType,
    Shape,
    ShapeType,
    TPIFuelArea,
)
from wps_shared.db.models.hfi_calc import FireCentre
from wps_shared.run_type import RunType
from wps_shared.schemas.fba import HfiThreshold

logger = logging.getLogger(__name__)


class HfiClassificationThresholdEnum(Enum):
    """Enum for the different HFI classification thresholds."""

    ADVISORY = "advisory"
    WARNING = "warning"


async def get_hfi_classification_threshold(
    session: AsyncSession, name: HfiClassificationThresholdEnum
) -> HfiClassificationThreshold:
    stmt = select(HfiClassificationThreshold).where(HfiClassificationThreshold.name == name.value)
    result = await session.execute(stmt)
    return result.scalars().first()


async def save_hfi(session: AsyncSession, hfi: ClassifiedHfi):
    session.add(hfi)


async def save_fuel_type(session: AsyncSession, fuel_type: FuelType):
    session.add(fuel_type)


async def get_fire_zone_unit_shape_type_id(session: AsyncSession):
    statement = select(ShapeType).where(ShapeType.name == "fire_zone_unit")
    result = await session.execute(statement)
    return result.scalars().first().id


async def get_fire_zone_units(session: AsyncSession, fire_zone_type_id: int):
    statement = select(Shape).where(Shape.shape_type == fire_zone_type_id)
    result = await session.execute(statement)
    return result.scalars().all()


async def get_table_srid(session: AsyncSession, model, geom_column: str = "geom"):
    schema = model.__table__.schema or "public"
    table_name = model.__tablename__

    stmt = select(func.Find_SRID(schema, table_name, geom_column))

    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_combustible_area(session: AsyncSession):
    """Get the combustible area for each "shape". This is slow, and we don't expect it to run
    in real time.

    This method isn't being used right now, but you can calculate the combustible area for each
    zone as follows:

    ```python
    from wps_shared.db.crud.auto_spatial_advisory import get_combustible_area
    from wps_shared.db.database import get_async_read_session_scope

    async with get_async_read_session_scope() as session:
    result = await get_combustible_area(session)

    for record in result:
        print(record)
        print(record['combustible_area']/record['zone_area'])
    ```

    """
    logger.info("starting zone/combustible area intersection query")
    perf_start = perf_counter()
    stmt = (
        select(
            Shape.id,
            Shape.source_identifier,
            Shape.geom.ST_Area().label("zone_area"),
            FuelType.geom.ST_Union()
            .ST_Intersection(Shape.geom)
            .ST_Area()
            .label("combustible_area"),
        )
        .join(FuelType, FuelType.geom.ST_Intersects(Shape.geom))
        .where(FuelType.fuel_type_id.not_in((-10000, 99, 100, 102, 103)))
        .group_by(Shape.id)
    )
    result = await session.execute(stmt)
    all_combustible = result.all()
    perf_end = perf_counter()
    delta = perf_end - perf_start
    logger.info("%f delta count before and after hfi area + zone/area intersection query", delta)
    return all_combustible


async def get_all_hfi_thresholds(session: AsyncSession) -> List[HfiClassificationThreshold]:
    """
    Retrieve all records from advisory_hfi_classification_threshold table.
    """
    logger.info("retrieving HFI classification threshold info...")
    stmt = select(HfiClassificationThreshold)
    result = await session.execute(stmt)

    thresholds = []

    for row in result.all():
        threshold_object = row[0]
        thresholds.append(
            HfiClassificationThreshold(
                id=threshold_object.id,
                description=threshold_object.description,
                name=threshold_object.name,
            )
        )

    return thresholds


async def get_all_hfi_thresholds_by_id(session: AsyncSession) -> dict[int, HfiThreshold]:
    """Retrieve all hfi thresholds and return them keyed by id.

    :param session: An async database session.
    :return: All hfi thresholds keyed by their ids
    """
    all_hfi_thresholds = await get_all_hfi_thresholds(session)
    all_hfi_thresholds_by_id = {}
    for hfi_threshold in all_hfi_thresholds:
        all_hfi_thresholds_by_id[int(hfi_threshold.id)] = HfiThreshold(
            id=hfi_threshold.id, name=hfi_threshold.name, description=hfi_threshold.description
        )
    return all_hfi_thresholds_by_id


async def get_all_sfms_fuel_types(session: AsyncSession) -> List[SFMSFuelType]:
    """
    Retrieve all records from sfms_fuel_types table excluding record IDs.
    """
    logger.info("retrieving SFMS fuel types info...")
    result = await get_all_sfms_fuel_type_records(session)

    fuel_types = []

    for row in result:
        fuel_type_object = row
        fuel_types.append(
            SFMSFuelType(
                fuel_type_id=fuel_type_object.fuel_type_id,
                fuel_type_code=fuel_type_object.fuel_type_code,
                description=fuel_type_object.description,
            )
        )

    return fuel_types


async def get_zone_source_ids_in_centre(session: AsyncSession, fire_centre_name: str):
    logger.info(
        f"retrieving fire zone source ids within {fire_centre_name} from advisory_shapes table"
    )

    stmt = (
        select(Shape.source_identifier)
        .join(FireCentre, FireCentre.id == Shape.fire_centre)
        .where(FireCentre.name == fire_centre_name)
    )
    result = await session.execute(stmt)

    all_results = result.scalars().all()

    return all_results


async def get_all_sfms_fuel_type_records(session: AsyncSession) -> List[SFMSFuelType]:
    """
    Retrieve all records from the sfms_fuel_types table.

    :param session: An async database session.
    :return: A list of all SFMSFuelType records.
    """
    stmt = select(SFMSFuelType)
    result = await session.execute(stmt)
    return result.scalars().all()


async def get_sfms_mixed_fuel_type(session: AsyncSession) -> SFMSFuelType:
    """
    Retrieve the fuel record corresponding to the M-1/M-2 fuel type.
    """
    stmt = select(SFMSFuelType).where(SFMSFuelType.fuel_type_code == "M-1/M-2")
    result = await session.execute(stmt)

    return result.scalar_one()


async def get_min_wind_speed_hfi_thresholds(
    session: AsyncSession,
    zone_source_ids: List[int],
    run_type: RunTypeEnum,
    run_datetime: datetime,
    for_date: date,
) -> dict[int, List[AdvisoryHFIWindSpeed]]:
    """
    Retrieve min wind speeds for each hfi thresholds, and key by source identifier
    """
    stmt = (
        select(AdvisoryHFIWindSpeed, Shape.source_identifier)
        .join(RunParameters, AdvisoryHFIWindSpeed.run_parameters == RunParameters.id)
        .join(Shape, AdvisoryHFIWindSpeed.advisory_shape_id == Shape.id)
        .where(
            Shape.source_identifier.in_(zone_source_ids),
            RunParameters.run_type == run_type.value,
            RunParameters.run_datetime == run_datetime,
            RunParameters.for_date == for_date,
        )
    )

    result = await session.execute(stmt)
    advisory_wind_speed_by_source_id = defaultdict(list)
    for advisory_hfi_wind_speed, source_id in result.all():
        advisory_wind_speed_by_source_id[int(source_id)].append(advisory_hfi_wind_speed)
    return advisory_wind_speed_by_source_id


async def get_precomputed_stats_for_shape(
    session: AsyncSession,
    run_type: RunTypeEnum,
    run_datetime: datetime,
    for_date: date,
    source_identifier: int,
) -> List[Row]:
    perf_start = perf_counter()
    stmt = (
        select(
            CriticalHours.start_hour,
            CriticalHours.end_hour,
            AdvisoryFuelStats.fuel_type,
            AdvisoryFuelStats.threshold,
            AdvisoryFuelStats.area,
            AdvisoryShapeFuels.fuel_area,
            AdvisoryHFIPercentConifer.min_percent_conifer,
        )
        .join(RunParameters, AdvisoryFuelStats.run_parameters == RunParameters.id)
        .join(
            CriticalHours,
            and_(
                CriticalHours.run_parameters == RunParameters.id,
                AdvisoryFuelStats.fuel_type == CriticalHours.fuel_type,
                AdvisoryFuelStats.advisory_shape_id == CriticalHours.advisory_shape_id,
            ),
            isouter=True,
        )
        .join(Shape, AdvisoryFuelStats.advisory_shape_id == Shape.id)
        .join(
            AdvisoryShapeFuels,
            and_(
                AdvisoryShapeFuels.fuel_type == AdvisoryFuelStats.fuel_type,
                AdvisoryShapeFuels.advisory_shape_id == Shape.id,
            ),
        )
        .join(
            AdvisoryHFIPercentConifer,
            and_(
                AdvisoryFuelStats.run_parameters == AdvisoryHFIPercentConifer.run_parameters,
                AdvisoryFuelStats.fuel_type == AdvisoryHFIPercentConifer.fuel_type,
                AdvisoryFuelStats.advisory_shape_id == AdvisoryHFIPercentConifer.advisory_shape_id,
            ),
            isouter=True,
        )
        .where(
            Shape.source_identifier == str(source_identifier),
            RunParameters.run_type == run_type.value,
            RunParameters.run_datetime == run_datetime,
            RunParameters.for_date == for_date,
        )
    )

    result = await session.execute(stmt)
    all_results = result.all()
    perf_end = perf_counter()
    delta = perf_end - perf_start
    logger.info("%f delta count before and after advisory stats query", delta)
    return all_results


async def get_fuel_type_stats_in_advisory_area(
    session: AsyncSession, advisory_shape_id: int, run_parameters_id: int
) -> List[Tuple[AdvisoryFuelStats, SFMSFuelType]]:
    stmt = (
        select(AdvisoryFuelStats, SFMSFuelType)
        .join_from(AdvisoryFuelStats, SFMSFuelType, AdvisoryFuelStats.fuel_type == SFMSFuelType.id)
        .filter(
            AdvisoryFuelStats.advisory_shape_id == advisory_shape_id,
            AdvisoryFuelStats.run_parameters == run_parameters_id,
        )
    )
    result = await session.execute(stmt)
    return result.all()


async def get_high_hfi_fuel_types_for_shape(
    session: AsyncSession,
    run_type: RunTypeEnum,
    run_datetime: datetime,
    for_date: date,
    shape_id: int,
) -> List[Row]:
    """
    Union of fuel types by fuel_type_id (1 multipolygon for each fuel type)
    Intersected with union of ClassifiedHfi for given run_type, run_datetime, and for_date
        for both 4K-10K and 10K+ HFI values
    Intersected with fire zone geom for a specific fire zone identified by ID
    """
    logger.info(
        "starting fuel types/high hfi/zone intersection query for fire zone %s", str(shape_id)
    )
    perf_start = perf_counter()

    stmt = (
        select(
            Shape.source_identifier,
            FuelType.fuel_type_id,
            ClassifiedHfi.threshold,
            func.sum(
                FuelType.geom.ST_Intersection(
                    ClassifiedHfi.geom.ST_Intersection(Shape.geom)
                ).ST_Area()
            ).label("area"),
        )
        .join_from(ClassifiedHfi, Shape, ClassifiedHfi.geom.ST_Intersects(Shape.geom))
        .join_from(ClassifiedHfi, FuelType, ClassifiedHfi.geom.ST_Intersects(FuelType.geom))
        .where(
            ClassifiedHfi.run_type == run_type.value,
            ClassifiedHfi.for_date == for_date,
            ClassifiedHfi.run_datetime == run_datetime,
            Shape.source_identifier == str(shape_id),
        )
        .group_by(Shape.source_identifier)
        .group_by(FuelType.fuel_type_id)
        .group_by(ClassifiedHfi.threshold)
        .order_by(FuelType.fuel_type_id)
        .order_by(ClassifiedHfi.threshold)
    )

    result = await session.execute(stmt)
    perf_end = perf_counter()
    delta = perf_end - perf_start
    logger.info(
        "%f delta count before and after fuel types/high hfi/zone intersection query", delta
    )
    return result.all()


async def get_high_hfi_fuel_types(
    session: AsyncSession, run_type: RunTypeEnum, run_datetime: datetime, for_date: date
) -> List[Row]:
    """
    Union of fuel types by fuel_type_id (1 multipolygon for each fuel type)
    Intersected with union of ClassifiedHfi for given run_type, run_datetime, and for_date
        for both 4K-10K and 10K+ HFI values
    """
    logger.info("starting fuel types/high hfi/zone intersection query")
    perf_start = perf_counter()

    stmt = (
        select(
            Shape.source_identifier,
            FuelType.fuel_type_id,
            ClassifiedHfi.threshold,
            func.sum(
                FuelType.geom.ST_Intersection(
                    ClassifiedHfi.geom.ST_Intersection(Shape.geom)
                ).ST_Area()
            ).label("area"),
        )
        .join_from(ClassifiedHfi, Shape, ClassifiedHfi.geom.ST_Intersects(Shape.geom))
        .join_from(ClassifiedHfi, FuelType, ClassifiedHfi.geom.ST_Intersects(FuelType.geom))
        .where(
            ClassifiedHfi.run_type == run_type.value,
            ClassifiedHfi.for_date == for_date,
            ClassifiedHfi.run_datetime == run_datetime,
        )
        .group_by(Shape.source_identifier)
        .group_by(FuelType.fuel_type_id)
        .group_by(ClassifiedHfi.threshold)
        .order_by(FuelType.fuel_type_id)
        .order_by(ClassifiedHfi.threshold)
    )

    logger.info(str(stmt))
    result = await session.execute(stmt)
    perf_end = perf_counter()
    delta = perf_end - perf_start
    logger.info(
        "%f delta count before and after fuel types/high hfi/zone intersection query", delta
    )
    return result.all()


async def get_hfi_area(
    session: AsyncSession,
    run_type: RunTypeEnum,
    run_datetime: datetime,
    for_date: date,
    fuel_type_raster_id: int,
) -> List[Row]:
    logger.info("gathering hfi area data")
    stmt = (
        select(
            Shape.id,
            Shape.source_identifier,
            CombustibleArea.combustible_area,
            HighHfiArea.id,
            HighHfiArea.advisory_shape_id,
            HighHfiArea.threshold,
            HighHfiArea.area.label("hfi_area"),
        )
        .join(HighHfiArea, HighHfiArea.advisory_shape_id == Shape.id)
        .join(RunParameters, RunParameters.id == HighHfiArea.run_parameters)
        .join(CombustibleArea, CombustibleArea.advisory_shape_id, Shape.id)
        .where(
            cast(RunParameters.run_type, String) == run_type.value,
            RunParameters.for_date == for_date,
            RunParameters.run_datetime == run_datetime,
            CombustibleArea.fuel_type_raster_id == fuel_type_raster_id,
        )
    )
    result = await session.execute(stmt)
    return result.all()


async def get_run_datetimes(
    session: AsyncSession, run_type: RunTypeEnum, for_date: date
) -> List[Row]:
    """
    Retrieve all distinct available run_datetimes for a given run_type and for_date, and return the run_datetimes
    in descending order (most recent is first)
    """
    stmt = (
        select(RunParameters.run_datetime)
        .where(RunParameters.run_type == run_type.value, RunParameters.for_date == for_date)
        .distinct()
        .order_by(RunParameters.run_datetime.desc())
    )
    result = await session.execute(stmt)
    return result.all()


async def get_sfms_bounds(session: AsyncSession):
    stmt = (
        select(
            extract("YEAR", RunParameters.for_date).label("year"),
            RunParameters.run_type,
            func.min(RunParameters.for_date).label("minDate"),
            func.max(RunParameters.for_date).label("maxDate"),
        )
        .group_by(extract("YEAR", RunParameters.for_date), RunParameters.run_type)
        .order_by("year")
    )
    result = await session.execute(stmt)
    return result.all()


async def get_most_recent_run_parameters(
    session: AsyncSession, run_type: RunTypeEnum, for_date: date
) -> List[Row]:
    """
    Retrieve the most recent sfms run parameters record for the specified run type and for date.

    :param session: Async database read session.
    :param run_type: Type of run (forecast or actual).
    :param for_date: The date of interest.
    :return: The most recent sfms run parameters record for the specified run type and for date, otherwise return None.
    """
    stmt = (
        select(RunParameters)
        .where(RunParameters.run_type == run_type.value, RunParameters.for_date == for_date)
        .distinct()
        .order_by(RunParameters.run_datetime.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.first()


async def get_run_parameters_by_id(session: AsyncSession, id: int) -> RunParameters:
    """
    Retrieve the RunParameters record with the specified id.

    :param session: Async database session.
    :param id: The id of the RunParameters record.
    :return: The RunParameters with the specified id.
    """
    stmt = select(RunParameters).where(RunParameters.id == id)
    result = await session.execute(stmt)
    return result.first()


async def get_high_hfi_area(
    session: AsyncSession, run_type: RunTypeEnum, run_datetime: datetime, for_date: date
) -> List[Row]:
    """For each fire zone, get the area of HFI polygons in that zone that fall within the
    4000 - 10000 range and the area of HFI polygons that exceed the 10000 threshold.
    """
    stmt = (
        select(
            HighHfiArea.id, HighHfiArea.advisory_shape_id, HighHfiArea.area, HighHfiArea.threshold
        )
        .join(RunParameters)
        .where(
            cast(RunParameters.run_type, String) == run_type.value,
            RunParameters.for_date == for_date,
            RunParameters.run_datetime == run_datetime,
        )
    )
    result = await session.execute(stmt)
    return result.all()


async def save_high_hfi_area(session: AsyncSession, high_hfi_area: HighHfiArea):
    session.add(high_hfi_area)


async def store_advisory_fuel_stats(
    session: AsyncSession,
    fuel_type_areas: dict,
    threshold: int,
    run_parameters_id: int,
    advisory_shape_id: int,
):
    """
    Creates AdvisoryFuelStats objects and save them in the wps database.

    :param : A dictionary keyed by fuel type code with value representing an area in square meters.
    :param threshold: The current threshold being processed, 1 = 4k-10k, 2 = > 10k.
    :param run_parameters_id: The RunParameter object id associated with the run_type, for_date and run_datetime of interest.
    :param advisory_shape_id: The id of advisory shape (eg. fire zone unit) the fuel type area has been calculated for.
    """
    sfms_fuel_types_dict = await get_fuel_types_id_dict(session)
    advisory_fuel_stats = []
    for key in fuel_type_areas:
        sfms_fuel_type_id = sfms_fuel_types_dict[key]
        advisory_fuel_stats.append(
            AdvisoryFuelStats(
                advisory_shape_id=advisory_shape_id,
                threshold=threshold,
                run_parameters=run_parameters_id,
                fuel_type=sfms_fuel_type_id,
                area=fuel_type_areas[key],
            )
        )
    await save_advisory_fuel_stats(session, advisory_fuel_stats)


async def save_advisory_fuel_stats(
    session: AsyncSession, advisory_fuel_stats: List[AdvisoryFuelStats]
):
    session.add_all(advisory_fuel_stats)


async def calculate_high_hfi_areas(
    session: AsyncSession, run_type: RunType, run_datetime: datetime, for_date: date
) -> List[Row]:
    """
    Given a 'run_parameters_id', which represents a unqiue combination of run_type, run_datetime
    and for_date, individually sum the areas in each firezone with:
        1. 4000 <= HFI < 10000 (aka 'advisory_area')
        2. HFI >= 10000 (aka 'warn_area')
    """
    logger.info("starting high HFI by zone intersection query")
    perf_start = perf_counter()

    stmt = (
        select(
            Shape.id.label("shape_id"),
            ClassifiedHfi.threshold.label("threshold"),
            func.sum(ClassifiedHfi.geom.ST_Intersection(Shape.geom).ST_Area()).label("area"),
        )
        .join_from(Shape, ClassifiedHfi, ClassifiedHfi.geom.ST_Intersects(Shape.geom))
        .where(ClassifiedHfi.run_type == run_type.value)
        .where(ClassifiedHfi.run_datetime == run_datetime)
        .where(ClassifiedHfi.for_date == for_date)
        .group_by(Shape.id)
        .group_by(ClassifiedHfi.threshold)
    )

    result = await session.execute(stmt)
    all_high_hfi = result.all()
    perf_end = perf_counter()
    delta = perf_end - perf_start
    logger.info(
        "%f delta count before and after calculate high HFI by zone intersection query", delta
    )
    return all_high_hfi


async def get_run_parameters_id(
    session: AsyncSession, run_type: RunType, run_datetime: datetime, for_date: date
) -> List[Row]:
    stmt = select(RunParameters.id).where(
        cast(RunParameters.run_type, String) == run_type.value,
        RunParameters.run_datetime == run_datetime,
        RunParameters.for_date == for_date,
    )
    result = await session.execute(stmt)
    return result.scalar()


async def save_run_parameters(
    session: AsyncSession, run_type: RunType, run_datetime: datetime, for_date: date
):
    logger.info(
        f"Writing run parameters. RunType: {run_type.value}; run_datetime: {run_datetime.isoformat()}; for_date: {for_date.isoformat()}"
    )
    stmt = (
        insert(RunParameters)
        .values(run_type=run_type.value, run_datetime=run_datetime, for_date=for_date)
        .on_conflict_do_nothing()
    )
    await session.execute(stmt)


async def save_advisory_elevation_stats(
    session: AsyncSession, advisory_elevation_stats: AdvisoryElevationStats
):
    session.add(advisory_elevation_stats)


async def save_advisory_elevation_tpi_stats(
    session: AsyncSession, advisory_elevation_stats: List[AdvisoryTPIStats]
):
    session.add_all(advisory_elevation_stats)


async def get_zonal_elevation_stats(
    session: AsyncSession,
    fire_zone_id: int,
    run_type: RunType,
    run_datetime: datetime,
    for_date: date,
) -> List[Row]:
    run_parameters_id = await get_run_parameters_id(session, run_type, run_datetime, for_date)
    stmt = select(Shape.id).where(Shape.source_identifier == str(fire_zone_id))
    result = await session.execute(stmt)
    shape_id = result.scalar()

    stmt = (
        select(
            AdvisoryElevationStats.advisory_shape_id,
            AdvisoryElevationStats.minimum,
            AdvisoryElevationStats.quartile_25,
            AdvisoryElevationStats.median,
            AdvisoryElevationStats.quartile_75,
            AdvisoryElevationStats.maximum,
            AdvisoryElevationStats.threshold,
        )
        .where(
            AdvisoryElevationStats.advisory_shape_id == shape_id,
            AdvisoryElevationStats.run_parameters == run_parameters_id,
        )
        .order_by(AdvisoryElevationStats.threshold)
    )

    return await session.execute(stmt)


async def get_zonal_tpi_stats(
    session: AsyncSession,
    fire_zone_id: int,
    run_type: RunType,
    run_datetime: datetime,
    for_date: date,
) -> Optional[AdvisoryTPIStats]:
    run_parameters_id = await get_run_parameters_id(session, run_type, run_datetime, for_date)
    stmt = select(Shape.id).where(Shape.source_identifier == str(fire_zone_id))
    result = await session.execute(stmt)
    shape_id = result.scalar()

    stmt = select(
        AdvisoryTPIStats.advisory_shape_id,
        AdvisoryTPIStats.valley_bottom,
        AdvisoryTPIStats.mid_slope,
        AdvisoryTPIStats.upper_slope,
        AdvisoryTPIStats.pixel_size_metres,
    ).where(
        AdvisoryTPIStats.advisory_shape_id == shape_id,
        AdvisoryTPIStats.run_parameters == run_parameters_id,
    )

    result = await session.execute(stmt)
    return result.first()


async def get_centre_tpi_stats(
    session: AsyncSession,
    fire_centre_name: str,
    run_type: RunType,
    run_datetime: datetime,
    for_date: date,
) -> AdvisoryTPIStats:
    run_parameters_id = await get_run_parameters_id(session, run_type, run_datetime, for_date)

    stmt = (
        select(
            AdvisoryTPIStats.advisory_shape_id,
            Shape.source_identifier,
            AdvisoryTPIStats.valley_bottom,
            AdvisoryTPIStats.mid_slope,
            AdvisoryTPIStats.upper_slope,
            AdvisoryTPIStats.pixel_size_metres,
        )
        .join(Shape, Shape.id == AdvisoryTPIStats.advisory_shape_id)
        .join(FireCentre, FireCentre.id == Shape.fire_centre)
        .where(
            FireCentre.name == fire_centre_name,
            AdvisoryTPIStats.run_parameters == run_parameters_id,
        )
    )

    result = await session.execute(stmt)
    return result.all()


async def get_fire_zone_tpi_fuel_areas(session: AsyncSession, fire_zone_id):
    stmt = (
        select(TPIFuelArea)
        .join(Shape, Shape.id == TPIFuelArea.advisory_shape_id)
        .where(Shape.source_identifier == fire_zone_id)
    )
    result = await session.execute(stmt)
    return result.all()


async def get_fire_centre_tpi_fuel_areas(session: AsyncSession, fire_centre_name: str):
    stmt = (
        select(TPIFuelArea.tpi_class, TPIFuelArea.fuel_area, Shape.source_identifier)
        .join(Shape, Shape.id == TPIFuelArea.advisory_shape_id)
        .join(FireCentre, FireCentre.id == Shape.fire_centre)
        .where(FireCentre.name == fire_centre_name)
    )
    result = await session.execute(stmt)
    return result.all()


async def get_provincial_rollup(
    session: AsyncSession,
    run_type: RunTypeEnum,
    run_datetime: datetime,
    for_date: date,
    fuel_type_raster_id: int,
) -> List[Row]:
    logger.info("gathering provincial rollup")
    run_parameter_id = await get_run_parameters_id(session, run_type, run_datetime, for_date)
    stmt = (
        select(
            Shape.id,
            Shape.source_identifier,
            CombustibleArea.combustible_area,
            Shape.placename_label,
            FireCentre.name.label("fire_centre_name"),
            HighHfiArea.id,
            HighHfiArea.advisory_shape_id,
            HighHfiArea.threshold,
            HighHfiArea.area.label("hfi_area"),
        )
        .join(FireCentre, FireCentre.id == Shape.fire_centre)
        .join(CombustibleArea, CombustibleArea.advisory_shape_id == Shape.id)
        .join(
            HighHfiArea,
            and_(
                HighHfiArea.advisory_shape_id == Shape.id,
                HighHfiArea.run_parameters == run_parameter_id,
            ),
            isouter=True,
        )
        .where(CombustibleArea.fuel_type_raster_id == fuel_type_raster_id)
    )
    result = await session.execute(stmt)
    return result.all()


async def get_containing_zone(session: AsyncSession, geometry: str, srid: int):
    geom = func.ST_Transform(func.ST_GeomFromText(geometry, srid), 3005)
    stmt = select(Shape.id).filter(func.ST_Contains(Shape.geom, geom))
    result = await session.execute(stmt)
    return result.first()


async def save_all_critical_hours(session: AsyncSession, critical_hours: List[CriticalHours]):
    session.add_all(critical_hours)


async def get_critical_hours_for_run_parameters(
    session: AsyncSession, run_type: RunTypeEnum, run_datetime: datetime, for_date: date
):
    stmt = (
        select(CriticalHours)
        .join_from(CriticalHours, RunParameters, CriticalHours.run_parameters == RunParameters.id)
        .where(
            RunParameters.run_type == run_type.value,
            RunParameters.run_datetime == run_datetime,
            RunParameters.for_date == for_date,
        )
        .group_by(CriticalHours.advisory_shape_id)
    )
    result = await session.execute(stmt)
    return result


async def get_fuel_types_code_dict(db_session: AsyncSession):
    """
    Gets a dictionary of fuel types keyed by fuel type code.

    :param db_session: An async database session.
    :return: A dictionary of fuel types keyed by fuel type code.
    """
    sfms_fuel_types = await get_all_sfms_fuel_type_records(db_session)
    fuel_types_dict = {}
    for fuel_type in sfms_fuel_types:
        fuel_types_dict[fuel_type.fuel_type_code] = fuel_type.id
    return fuel_types_dict


async def get_fuel_types_id_dict(db_session: AsyncSession):
    """
    Gets a dictionary of sfms_fuel_types table id's keyed by fuel_type_id (raster values).

    :param db_session: An async database session.
    :return: Dict of sfms_fuel_types table id's keyed by fuel_type_id (raster values).
    """
    sfms_fuel_types = await get_all_sfms_fuel_type_records(db_session)
    fuel_types_dict = {}
    for fuel_type in sfms_fuel_types:
        fuel_types_dict[fuel_type.fuel_type_id] = fuel_type.id
    return fuel_types_dict
