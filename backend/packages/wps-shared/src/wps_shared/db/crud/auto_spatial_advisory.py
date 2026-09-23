import logging
from collections import defaultdict
from datetime import date, datetime
from time import perf_counter
from typing import List, Optional, Tuple

from sqlalchemy import Integer, String, and_, case, cast, desc, extract, func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine.row import Row
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from wps_shared.db.models.auto_spatial_advisory import (
    AdvisoryFuelStats,
    AdvisoryHFIPercentConifer,
    AdvisoryHFIWindSpeed,
    AdvisoryShapeFuels,
    AdvisoryTPIStats,
    AdvisoryZoneStatus,
    CombustibleArea,
    CriticalHours,
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
from wps_shared.db.models.fuel_type_raster import FuelTypeRaster
from wps_shared.db.models.psu import FireCentre
from wps_shared.run_type import RunType
from wps_shared.schemas.auto_spatial_advisory import ZoneAdvisoryStatus
from wps_shared.schemas.fba import FireShapeStatusDetail, HfiArea, HfiThreshold

logger = logging.getLogger(__name__)

ADVISORY_THRESHOLD = 20

advisory_status_case = case(
    (
        AdvisoryZoneStatus.warning_percentage > ADVISORY_THRESHOLD,
        HfiClassificationThresholdEnum.WARNING.value,
    ),
    (
        AdvisoryZoneStatus.advisory_percentage + AdvisoryZoneStatus.warning_percentage
        > ADVISORY_THRESHOLD,
        HfiClassificationThresholdEnum.ADVISORY.value,
    ),
    else_=None,
)


async def count_rows_by_fuel_type_raster_id(
    session: AsyncSession, model, fuel_type_raster_id: int
) -> int:
    """
    Count rows for a fuel-grid-derived advisory table.

    :param session: An async database session.
    :param model: SQLAlchemy model with a fuel_type_raster_id column.
    :param fuel_type_raster_id: Fuel type raster id to count rows for.
    :return: Row count for the fuel type raster.
    """
    stmt = (
        select(func.count())
        .select_from(model)
        .where(model.fuel_type_raster_id == fuel_type_raster_id)
    )
    result = await session.execute(stmt)
    return result.scalar_one()


async def count_advisory_shape_fuel_duplicates(
    session: AsyncSession, fuel_type_raster_id: int
) -> int:
    """
    Count duplicate advisory_shape_fuels rows for a fuel type raster.

    :param session: An async database session.
    :param fuel_type_raster_id: Fuel type raster id to check.
    :return: Number of duplicate advisory shape and fuel type combinations.
    """
    duplicates = (
        select(
            AdvisoryShapeFuels.advisory_shape_id,
            AdvisoryShapeFuels.fuel_type,
            AdvisoryShapeFuels.fuel_type_raster_id,
        )
        .where(AdvisoryShapeFuels.fuel_type_raster_id == fuel_type_raster_id)
        .group_by(
            AdvisoryShapeFuels.advisory_shape_id,
            AdvisoryShapeFuels.fuel_type,
            AdvisoryShapeFuels.fuel_type_raster_id,
        )
        .having(func.count() > 1)
        .subquery()
    )
    result = await session.execute(select(func.count()).select_from(duplicates))
    return result.scalar_one()


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


async def get_hfi_threshold_ids(session: AsyncSession) -> dict[str, int]:
    """
    Returns dict of {name: id} for advisory, warning threshold records
    """
    stmt = select(HfiClassificationThreshold.id, HfiClassificationThreshold.name)
    result = await session.execute(stmt)
    return {name: id_ for id_, name in result.all()}


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


async def get_all_zone_source_ids(session: AsyncSession):
    """
    Retrieve the ids of all fire shapes (aka fire zone units).

    :param session: An async database session.
    :return: A list of the ids of all fire shapes/fire zone units.
    """
    logger.info("retrieving all fire zone source ids from advisory_shapes table")
    stmt = select(Shape.source_identifier)
    result = await session.execute(stmt)
    return result.scalars().all()


async def get_advisory_shape_ids_by_source_identifier(
    session: AsyncSession,
) -> dict[int, int]:
    """Return advisory shape database IDs keyed by raster source identifier."""
    result = await session.execute(select(Shape.source_identifier, Shape.id))
    return {int(source_identifier): shape_id for source_identifier, shape_id in result}


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
    fuel_type_raster_id: int,
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
                AdvisoryShapeFuels.fuel_type_raster_id == AdvisoryFuelStats.fuel_type_raster_id,
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
            AdvisoryShapeFuels.fuel_type_raster_id == fuel_type_raster_id,
        )
    )

    result = await session.execute(stmt)
    all_results = result.all()
    perf_end = perf_counter()
    delta = perf_end - perf_start
    logger.info("%f delta count before and after advisory stats query", delta)
    return all_results


async def get_fuel_type_stats_in_advisory_area(
    session: AsyncSession, advisory_shape_id: int, run_parameters_id: int, fuel_type_raster_id: int
) -> List[Tuple[AdvisoryFuelStats, SFMSFuelType]]:
    stmt = (
        select(AdvisoryFuelStats, SFMSFuelType)
        .join_from(AdvisoryFuelStats, SFMSFuelType, AdvisoryFuelStats.fuel_type == SFMSFuelType.id)
        .filter(
            AdvisoryFuelStats.advisory_shape_id == advisory_shape_id,
            AdvisoryFuelStats.run_parameters == run_parameters_id,
            AdvisoryFuelStats.fuel_type_raster_id == fuel_type_raster_id,
        )
    )
    result = await session.execute(stmt)
    return result.all()


async def get_hfi_area(
    session: AsyncSession,
    run_type: RunTypeEnum,
    run_datetime: datetime,
    for_date: date,
    fuel_type_raster_id: int,
) -> List[HfiArea]:
    logger.info("gathering hfi area data")
    stmt = (
        select(
            Shape.id.label("shape_id"),
            Shape.source_identifier,
            CombustibleArea.combustible_area,
            HighHfiArea.id.label("high_hfi_area_id"),
            HighHfiArea.threshold,
            HighHfiArea.area.label("hfi_area"),
        )
        .join(HighHfiArea, HighHfiArea.advisory_shape_id == Shape.id)
        .join(RunParameters, RunParameters.id == HighHfiArea.run_parameters)
        .join(CombustibleArea, CombustibleArea.advisory_shape_id == Shape.id)
        .where(
            cast(RunParameters.run_type, String) == run_type.value,
            RunParameters.for_date == for_date,
            RunParameters.run_datetime == run_datetime,
            CombustibleArea.fuel_type_raster_id == fuel_type_raster_id,
        )
    )
    result = await session.execute(stmt)
    return [HfiArea.model_validate(row) for row in result.mappings().all()]


async def get_run_datetimes(
    session: AsyncSession, run_type: RunTypeEnum, for_date: date
) -> List[Row]:
    """
    Retrieve all distinct available run_datetimes for a given run_type and for_date, and return the run_datetimes
    in descending order (most recent is first)
    """
    stmt = (
        select(RunParameters.run_datetime)
        .where(
            RunParameters.run_type == run_type.value,
            RunParameters.for_date == for_date,
            RunParameters.complete.is_(True),
        )
        .distinct()
        .order_by(RunParameters.run_datetime.desc())
    )
    result = await session.execute(stmt)
    return result.all()


async def get_most_recent_run_datetime_for_date(session: AsyncSession, for_date: date):
    """
    Get the most recent sfms run for the given for date whether it is an actual or forecast.

    :param session: An async db session.
    :param for_date: The date of interest.
    """
    stmt = (
        select(RunParameters)
        .where(RunParameters.for_date == for_date, RunParameters.complete.is_(True))
        .order_by(RunParameters.run_datetime.desc())
    )
    result = await session.execute(stmt)
    return result.scalars().first()


async def get_most_recent_run_datetime_for_date_range(
    session: AsyncSession, start_date: date, end_date: date
):
    """
    Return the most recent SFMS run parameters for each date from the start_date to the end_date (inclusive).

    :param session: An async database session.
    :param start_date: The start date.
    :param end_date: The end date.
    :return: A list of the most recent SFMS run parameter per date within the specified range.
    """
    subquery = (
        select(
            RunParameters,
            func.row_number()
            .over(partition_by=RunParameters.for_date, order_by=desc(RunParameters.run_datetime))
            .label("row_num"),
        )
        .where(
            RunParameters.for_date.between(start_date, end_date), RunParameters.complete.is_(True)
        )
        .subquery()
    )

    # Alias the subquery for querying
    run_params_alias = aliased(RunParameters, subquery)

    # Final query: only rows with row_num == 1
    stmt = select(run_params_alias).where(subquery.c.row_num == 1)
    result = await session.execute(stmt)
    return result.scalars()


async def get_sfms_bounds(session: AsyncSession):
    stmt = (
        select(
            extract("YEAR", RunParameters.for_date).label("year"),
            RunParameters.run_type,
            func.min(RunParameters.for_date).label("minDate"),
            func.max(RunParameters.for_date).label("maxDate"),
        )
        .where(RunParameters.complete.is_(True))
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
        .where(
            RunParameters.run_type == run_type.value,
            RunParameters.for_date == for_date,
        )
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


async def get_run_parameters(
    session: AsyncSession, run_type: RunTypeEnum, run_datetime: datetime, for_date: date
) -> RunParameters:
    """
    Retrieve the RunParameters record for the specified run type, run datetime, and for date.

    :param session: Async database session.
    :param run_type: Type of run (forecast or actual).
    :param run_datetime: The datetime of the run.
    :param for_date: The date of interest.
    :return: The RunParameters record for the specified run type, run datetime, and for date.
    """
    stmt = select(RunParameters).where(
        RunParameters.run_type == run_type.value,
        RunParameters.run_datetime == run_datetime,
        RunParameters.for_date == for_date,
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_run_parameters_id(
    session: AsyncSession,
    run_type: RunType,
    run_datetime: datetime,
    for_date: date,
) -> Optional[int]:
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


async def mark_run_parameter_complete(
    session: AsyncSession, run_type: RunType, run_datetime: datetime, for_date: date
) -> bool:
    """Mark a run complete and return whether this call performed the transition."""
    run_parameters = await get_run_parameters(session, run_type, run_datetime, for_date)
    if not run_parameters:
        raise RuntimeError(f"No run parameters found for {run_type} {run_datetime} {for_date}")

    if run_parameters.complete:
        logger.info(
            f"Run parameters already marked as complete for {run_type} {run_datetime} {for_date}"
        )
        return False

    stmt = (
        update(RunParameters)
        .where(RunParameters.id == run_parameters.id, RunParameters.complete.is_not(True))
        .values(complete=True)
        .returning(RunParameters.id)
    )
    result = await session.execute(stmt)
    if result.scalar_one_or_none() is None:
        logger.info(
            "Run parameters were marked complete by another processor for %s %s %s",
            run_type,
            run_datetime,
            for_date,
        )
        return False

    logger.info(
        f"Marking run parameter {run_parameters.id} as complete for {run_type} {run_datetime} {for_date}"
    )
    return True


async def save_advisory_elevation_tpi_stats(
    session: AsyncSession, advisory_elevation_stats: List[AdvisoryTPIStats]
):
    session.add_all(advisory_elevation_stats)


async def get_centre_tpi_stats(
    session: AsyncSession,
    fire_centre_name: str,
    run_type: RunType,
    run_datetime: datetime,
    for_date: date,
):
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


async def get_tpi_stats(
    session: AsyncSession, run_type: RunType, run_datetime: datetime, for_date: date
):
    """
    Return the TPI stats for all fire zone units for the SFMS run parameter corresponding to the provided run type, for date and run date time.

    :param session: An async database session.
    :param run_type: The RunType.
    :param run_datetime: The date and time of the SFMS run.
    :param for_date: The for date of the SFMS run.
    :return: TPI fuel stats for all fire zone units.
    """
    run_parameters_id = await get_run_parameters_id(session, run_type, run_datetime, for_date)
    stmt = (
        select(
            AdvisoryTPIStats.advisory_shape_id,
            Shape.source_identifier,
            AdvisoryTPIStats.valley_bottom,
            AdvisoryTPIStats.mid_slope,
            AdvisoryTPIStats.upper_slope,
            AdvisoryTPIStats.pixel_size_metres,
            FireCentre.id,
            FireCentre.name,
        )
        .join(Shape, Shape.id == AdvisoryTPIStats.advisory_shape_id)
        .join(FireCentre, FireCentre.id == Shape.fire_centre)
        .where(
            AdvisoryTPIStats.run_parameters == run_parameters_id,
        )
    )

    result = await session.execute(stmt)
    return result.all()


async def get_fire_centre_tpi_fuel_areas(
    session: AsyncSession, fire_centre_name: str, fuel_type_raster_id: int
):
    stmt = (
        select(TPIFuelArea.tpi_class, TPIFuelArea.fuel_area, Shape.source_identifier)
        .join(Shape, Shape.id == TPIFuelArea.advisory_shape_id)
        .join(FireCentre, FireCentre.id == Shape.fire_centre)
        .where(
            FireCentre.name == fire_centre_name,
            TPIFuelArea.fuel_type_raster_id == fuel_type_raster_id,
        )
    )
    result = await session.execute(stmt)
    return result.all()


async def get_tpi_fuel_areas(session: AsyncSession, fuel_type_raster_id: int):
    """
    Retrieve TPI fuel stats for all fire zone units in the province.

    :param session: An async database session.
    :param fuel_type_raster_id: The fuel grid raster id.
    :return: The TPI fuel stats for all fire zone units.
    """
    stmt = (
        select(
            TPIFuelArea.tpi_class,
            TPIFuelArea.fuel_area,
            Shape.source_identifier,
            FireCentre.id,
            FireCentre.name,
        )
        .join(Shape, Shape.id == TPIFuelArea.advisory_shape_id)
        .join(FireCentre, FireCentre.id == Shape.fire_centre)
        .where(
            TPIFuelArea.fuel_type_raster_id == fuel_type_raster_id,
        )
    )
    result = await session.execute(stmt)
    return result.all()


async def get_provincial_rollup(
    session: AsyncSession,
    run_type: RunTypeEnum,
    run_datetime: datetime,
    for_date: date,
) -> List[FireShapeStatusDetail]:
    logger.info("gathering provincial rollup")
    run_parameter_id = await get_run_parameters_id(session, run_type, run_datetime, for_date)

    # subquery to find the fuel_type_raster_id for the most recent year
    # for AdvisoryZoneStatus records matching the run_parameters
    most_recent_raster_subquery = (
        select(FuelTypeRaster.id)
        .join(
            AdvisoryZoneStatus,
            AdvisoryZoneStatus.fuel_type_raster_id == FuelTypeRaster.id,
        )
        .where(AdvisoryZoneStatus.run_parameters == run_parameter_id)
        .order_by(FuelTypeRaster.year.desc())
        .limit(1)
        .scalar_subquery()
    )

    stmt = (
        select(
            Shape.source_identifier.label("fire_shape_id"),
            Shape.placename_label.label("fire_shape_name"),
            FireCentre.name.label("fire_centre_name"),
            advisory_status_case.label("status"),
        )
        .join(FireCentre, FireCentre.id == Shape.fire_centre)
        .join(
            AdvisoryZoneStatus,
            and_(
                AdvisoryZoneStatus.advisory_shape_id == Shape.id,
                AdvisoryZoneStatus.run_parameters == run_parameter_id,
                AdvisoryZoneStatus.fuel_type_raster_id == most_recent_raster_subquery,
            ),
            isouter=True,
        )
    )
    result = await session.execute(stmt)
    return [FireShapeStatusDetail.model_validate(row) for row in result.mappings().all()]


async def get_zones_with_advisories(
    session: AsyncSession, run_type: RunTypeEnum, run_datetime: datetime, for_date: date
) -> list[ZoneAdvisoryStatus]:
    logger.info("gathering zones with advisories/warnings")
    run_parameter_id = await get_run_parameters_id(session, run_type, run_datetime, for_date)
    stmt = (
        select(
            AdvisoryZoneStatus.advisory_shape_id,
            Shape.fire_centre.label("fire_centre_id"),
            Shape.source_identifier,
            Shape.placename_label,
            advisory_status_case.label("status"),
        )
        .where(AdvisoryZoneStatus.run_parameters == run_parameter_id)
        .where(advisory_status_case.isnot(None))
        .join(Shape, Shape.id == AdvisoryZoneStatus.advisory_shape_id)
    )
    result = await session.execute(stmt)
    return [ZoneAdvisoryStatus.model_validate(row) for row in result.mappings().all()]


async def save_all_critical_hours(session: AsyncSession, critical_hours: List[CriticalHours]):
    session.add_all(critical_hours)


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


async def gather_zone_status_inputs(
    session: AsyncSession,
    run_type: RunType,
    run_datetime: datetime,
    for_date: date,
    fuel_type_raster_id: int,
):
    thresholds_lut = await get_hfi_threshold_ids(session)

    hfi_rows = await get_hfi_area(
        session,
        RunTypeEnum(run_type.value),
        run_datetime,
        for_date,
        fuel_type_raster_id,
    )

    return thresholds_lut, hfi_rows


async def get_fire_centre_info(db_session: AsyncSession):
    stmt = (
        select(cast(Shape.source_identifier, Integer), Shape.placename_label, FireCentre.name)
        .join(ShapeType, ShapeType.id == Shape.shape_type)
        .join(FireCentre, FireCentre.id == Shape.fire_centre)
        .where(ShapeType.name == "fire_zone_unit")
    )
    result = await db_session.execute(stmt)
    return result.all()
