from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from wps_shared.db.models.fire_watch import (
    FireWatch,
    FireWatchWeather,
    PrescriptionStatus,
)
from wps_shared.db.models.hfi_calc import FireCentre
from wps_shared.db.models.weather_models import PredictionModel, PredictionModelRunTimestamp
from wps_shared.weather_models import ModelEnum


def fire_watch_to_dict(fire_watch: FireWatch) -> dict:
    """Convert FireWatch object to a dict of column values for insert/update."""
    return {
        "burn_location": fire_watch.burn_location,
        "burn_window_end": fire_watch.burn_window_end,
        "burn_window_start": fire_watch.burn_window_start,
        "contact_email": fire_watch.contact_email,
        "create_timestamp": fire_watch.create_timestamp,
        "create_user": fire_watch.create_user,
        "fire_centre": fire_watch.fire_centre,
        "station_code": fire_watch.station_code,
        "status": fire_watch.status,
        "title": fire_watch.title,
        "update_timestamp": fire_watch.update_timestamp,
        "update_user": fire_watch.update_user,
        # Fuel parameters
        "fuel_type": fire_watch.fuel_type,
        "percent_conifer": fire_watch.percent_conifer,
        "percent_dead_fir": fire_watch.percent_dead_fir,
        "percent_grass_curing": fire_watch.percent_grass_curing,
        # Weather parameters
        "temp_min": fire_watch.temp_min,
        "temp_preferred": fire_watch.temp_preferred,
        "temp_max": fire_watch.temp_max,
        "rh_min": fire_watch.rh_min,
        "rh_preferred": fire_watch.rh_preferred,
        "rh_max": fire_watch.rh_max,
        "wind_speed_min": fire_watch.wind_speed_min,
        "wind_speed_preferred": fire_watch.wind_speed_preferred,
        "wind_speed_max": fire_watch.wind_speed_max,
        # FWI and FBP parameters
        "ffmc_min": fire_watch.ffmc_min,
        "ffmc_preferred": fire_watch.ffmc_preferred,
        "ffmc_max": fire_watch.ffmc_max,
        "dmc_min": fire_watch.dmc_min,
        "dmc_preferred": fire_watch.dmc_preferred,
        "dmc_max": fire_watch.dmc_max,
        "dc_min": fire_watch.dc_min,
        "dc_preferred": fire_watch.dc_preferred,
        "dc_max": fire_watch.dc_max,
        "isi_min": fire_watch.isi_min,
        "isi_preferred": fire_watch.isi_preferred,
        "isi_max": fire_watch.isi_max,
        "bui_min": fire_watch.bui_min,
        "bui_preferred": fire_watch.bui_preferred,
        "bui_max": fire_watch.bui_max,
        "hfi_min": fire_watch.hfi_min,
        "hfi_preferred": fire_watch.hfi_preferred,
        "hfi_max": fire_watch.hfi_max,
    }


async def get_all_fire_watches(session: AsyncSession):
    statement = select(FireWatch, FireCentre).join(
        FireCentre, FireWatch.fire_centre == FireCentre.id
    )
    result = await session.execute(statement)
    return result.all()


async def get_fire_centre_by_name(session: AsyncSession, name: str) -> FireCentre:
    statement = select(FireCentre).where(FireCentre.name.ilike(name))
    result = await session.execute(statement)
    return result.scalar_one()


async def get_fire_watch_by_id(session: AsyncSession, id: int):
    statement = (
        select(FireWatch, FireCentre)
        .join(FireCentre, FireWatch.fire_centre == FireCentre.id)
        .where(FireWatch.id == id)
    )
    result = await session.execute(statement)
    return result.first()


async def save_fire_watch(session: AsyncSession, fire_watch: FireWatch):
    """
    Save a new FireWatch and return the id of the new record.

    :param session: Async db session.
    :param fire_watch: The FireWatch record to save.
    :return: The id of the new FireWatch record.
    """
    statement = insert(FireWatch).values(**fire_watch_to_dict(fire_watch)).returning(FireWatch.id)
    result = await session.execute(statement)
    return result.scalar_one()


async def update_fire_watch(
    session: AsyncSession, fire_watch_id: int, fire_watch: FireWatch
) -> FireWatch:
    """
    Update an existing FireWatch record.

    :param session: Async db session.
    :param fire_watch_id: The id of the FireWatch record to update.
    :param fire_watch: The FireWatch record with updated values.
    :return: The updated FireWatch record.
    """
    statement = (
        update(FireWatch)
        .where(FireWatch.id == fire_watch_id)
        .values(**fire_watch_to_dict(fire_watch))
        .returning(FireWatch)
    )
    result = await session.execute(statement)
    return result.scalar_one()


async def get_fire_centres(session: AsyncSession):
    statement = select(FireCentre)
    result = await session.execute(statement)
    return result.scalars()


async def get_all_prescription_status(session: AsyncSession) -> dict[str, int]:
    """
    Returns dict of {name: id} for all prescription status records.
    """
    stmt = select(PrescriptionStatus.id, PrescriptionStatus.name)
    result = await session.execute(stmt)
    return {name: id for id, name in result.all()}


async def get_fire_watch_weather_by_model_run_parameter_id(
    session: AsyncSession, prediction_model_run_timestamp_id: int
):
    statement = select(FireWatchWeather).where(
        FireWatchWeather.prediction_model_run_timestamp_id == prediction_model_run_timestamp_id
    )
    result = await session.execute(statement)
    return result.scalars().all()


async def get_fire_watch_weather_by_fire_watch_id_and_model_run(
    session: AsyncSession, fire_watch_id: int, prediction_model_run_timestamp_id: int
):
    stmt = select(FireWatchWeather).where(
        FireWatchWeather.fire_watch_id == fire_watch_id,
        FireWatchWeather.prediction_model_run_timestamp_id == prediction_model_run_timestamp_id,
    )

    result = await session.execute(stmt)
    existing_record = result.scalars().all()

    return existing_record


async def get_fire_watch_weather_by_model_with_prescription_status_all(
    session: AsyncSession, prediction_model_run_timestamp_id: int
):
    statement = (
        select(FireWatchWeather, PrescriptionStatus.name)
        .join(PrescriptionStatus, PrescriptionStatus.id == FireWatchWeather.in_prescription)
        .where(
            FireWatchWeather.prediction_model_run_timestamp_id == prediction_model_run_timestamp_id
        )
    )
    result = await session.execute(statement)
    return result.all()


async def get_fire_watch_weather_by_model_with_prescription_status(
    session: AsyncSession, fire_watch_id: int, prediction_model_run_timestamp_id: int
):
    statement = (
        select(FireWatchWeather, PrescriptionStatus.name)
        .join(PrescriptionStatus, PrescriptionStatus.id == FireWatchWeather.in_prescription)
        .where(
            FireWatchWeather.fire_watch_id == fire_watch_id,
            FireWatchWeather.prediction_model_run_timestamp_id == prediction_model_run_timestamp_id,
        )
    )
    result = await session.execute(statement)
    return result.all()


async def get_latest_processed_model_run_id_for_fire_watch_model(
    session: AsyncSession, model: ModelEnum
) -> int:
    stmt = (
        select(PredictionModelRunTimestamp.id)
        .join(
            FireWatchWeather,
            FireWatchWeather.prediction_model_run_timestamp_id == PredictionModelRunTimestamp.id,
        )
        .join(
            PredictionModel, PredictionModel.id == PredictionModelRunTimestamp.prediction_model_id
        )
        .where(PredictionModel.abbreviation == model.value)
        .order_by(PredictionModelRunTimestamp.prediction_run_timestamp.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar()
