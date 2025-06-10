from datetime import datetime, timedelta
from sqlalchemy import func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from wps_shared.db.models.fire_watch import (
    FireWatch,
    FireWatchWeather,
    PrescriptionStatus,
)
from wps_shared.db.models.hfi_calc import FireCentre
from wps_shared.db.models.weather_models import PredictionModelRunTimestamp
from wps_shared.utils.time import get_utc_now


def fire_watch_to_dict(fire_watch: FireWatch) -> dict:
    """Convert FireWatch object to a dict of column values for insert/update."""
    return {
        c.name: getattr(fire_watch, c.name) for c in fire_watch.__table__.columns if c.name != "id"
    }


async def get_all_fire_watches(session: AsyncSession):
    statement = select(FireWatch, FireCentre).join(
        FireCentre, FireWatch.fire_centre == FireCentre.id
    )
    result = await session.execute(statement)
    return result.all()


async def get_fire_watches_missing_weather_for_run(
    session: AsyncSession, prediction_model_run_timestamp_id: int
):
    """
    Return a list of FireWatch objects that do NOT have weather for the given prediction_id.
    """
    stmt = (
        select(FireWatch)
        .outerjoin(
            FireWatchWeather,
            (FireWatch.id == FireWatchWeather.fire_watch_id)
            & (
                FireWatchWeather.prediction_model_run_timestamp_id
                == prediction_model_run_timestamp_id
            ),
        )
        .where(FireWatchWeather.id.is_(None))
    )
    result = await session.execute(stmt)
    return result.scalars().all()


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


async def get_all_fire_watch_weather_with_prescription_status(
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


async def get_latest_processed_model_run_id_in_fire_watch_weather(session: AsyncSession) -> int:
    stmt = select(func.max(FireWatchWeather.prediction_model_run_timestamp_id))
    result = await session.execute(stmt)
    return result.scalar()
