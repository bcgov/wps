from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import wps_shared.utils.time as time_utils
from wps_shared.db.models.smurfi import (
    SpotDescriptiveWeather,
    SpotForecast,
    SpotRequest,
    SpotSubscriber,
    SpotSubscriberStatusEnum,
    SpotTabularWeather,
)


async def create_spot_request(session: AsyncSession, spot_request: SpotRequest):
    session.add(spot_request)
    await session.flush()
    return spot_request


async def create_spot_forecast(session: AsyncSession, spot_forecast: SpotForecast):
    session.add(spot_forecast)
    await session.flush()
    return spot_forecast


async def sync_spot_subscribers(
    session: AsyncSession, spot_request_id: int, emails: list[str]
) -> list[SpotSubscriber]:
    result = await session.execute(
        select(SpotSubscriber).where(SpotSubscriber.spot_request_id == spot_request_id)
    )
    existing = result.scalars().all()

    active_emails = set(emails)
    existing_by_email = {s.email: s for s in existing}
    active_subscribers = []

    for subscriber in existing:
        target_status = (
            SpotSubscriberStatusEnum.ACTIVE.value
            if subscriber.email in active_emails
            else SpotSubscriberStatusEnum.INACTIVE.value
        )
        if subscriber.subscriber_status != target_status:
            subscriber.subscriber_status = target_status
        if target_status == SpotSubscriberStatusEnum.ACTIVE.value:
            active_subscribers.append(subscriber)

    for email in active_emails:
        if email not in existing_by_email:
            new_subscriber = SpotSubscriber(spot_request_id=spot_request_id, email=email)
            session.add(new_subscriber)
            active_subscribers.append(new_subscriber)

    await session.flush()
    return active_subscribers


async def create_spot_tabular_weather(
    session: AsyncSession, spot_tabular_weather: SpotTabularWeather
):
    session.add(spot_tabular_weather)
    await session.flush()
    return spot_tabular_weather


async def create_spot_descriptive_weather(
    session: AsyncSession, spot_descriptive_weather: SpotDescriptiveWeather
):
    session.add(spot_descriptive_weather)
    await session.flush()
    return spot_descriptive_weather


async def update_spot_request(session: AsyncSession, updated: SpotRequest):
    result = await session.execute(select(SpotRequest).where(SpotRequest.id == updated.id))
    existing = result.scalar_one_or_none()
    if existing is not None:
        existing.request_reference = updated.request_reference
        existing.fire_number = updated.fire_number
        existing.fire_centre = updated.fire_centre
        existing.status = updated.status
        existing.requestor_name = updated.requestor_name
        existing.requestor_idir = updated.requestor_idir
        existing.requestor_email = updated.requestor_email
        existing.request_frequency = updated.request_frequency
        existing.request_type = updated.request_type
        existing.aspect = updated.aspect
        existing.elevation = updated.elevation
        existing.geographic_description = updated.geographic_description
        existing.additional_information = updated.additional_information
        existing.geom = updated.geom
        existing.requested_at = updated.requested_at
        existing.start_at = updated.start_at
        existing.end_at = updated.end_at
        await session.flush()
    return existing


async def update_spot_forecast(session: AsyncSession, updated: SpotForecast):
    result = await session.execute(select(SpotForecast).where(SpotForecast.id == updated.id))
    existing = result.scalar_one_or_none()
    if existing is not None:
        existing.forecaster_name = updated.forecaster_name
        existing.forecaster_email = updated.forecaster_email
        existing.forecaster_phone = updated.forecaster_phone
        existing.synopsis = updated.synopsis
        existing.inversion_and_venting = updated.inversion_and_venting
        existing.outlook = updated.outlook
        existing.confidence = updated.confidence
        existing.fire_size = updated.fire_size
        existing.representative_station_codes = updated.representative_station_codes
        existing.for_date = updated.for_date
        await session.flush()
    return existing


async def update_spot_tabular_weather(session: AsyncSession, updated: SpotTabularWeather):
    result = await session.execute(
        select(SpotTabularWeather).where(
            SpotTabularWeather.id == updated.id,
            SpotTabularWeather.spot_forecast_id == updated.spot_forecast_id,
        )
    )
    existing = result.scalar_one_or_none()
    if existing is not None:
        existing.forecast_time = updated.forecast_time
        existing.temperature = updated.temperature
        existing.relative_humidity = updated.relative_humidity
        existing.wind = updated.wind
        existing.probability_of_precipitation = updated.probability_of_precipitation
        existing.precipitation_amount = updated.precipitation_amount
        await session.flush()
    return existing


async def update_spot_descriptive_weather(session: AsyncSession, updated: SpotDescriptiveWeather):
    result = await session.execute(
        select(SpotDescriptiveWeather).where(
            SpotDescriptiveWeather.id == updated.id,
            SpotDescriptiveWeather.spot_forecast_id == updated.spot_forecast_id,
        )
    )
    existing = result.scalar_one_or_none()
    if existing is not None:
        existing.period = updated.period
        existing.temperature = updated.temperature
        existing.relative_humidity = updated.relative_humidity
        existing.conditions = updated.conditions
        await session.flush()
    return existing


async def get_spot_requests_for_year(session: AsyncSession, year: int):
    year_start = datetime(year, 1, 1, tzinfo=timezone.utc)
    year_end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    result = await session.execute(
        select(SpotRequest)
        .where(SpotRequest.start_at >= year_start, SpotRequest.start_at < year_end)
        .options(selectinload(SpotRequest.spot_subscribers))
    )
    return result.scalars().all()


async def update_spot_subscriber_status(
    session: AsyncSession, subscriber_id: int, status: SpotSubscriberStatusEnum
):
    result = await session.execute(select(SpotSubscriber).where(SpotSubscriber.id == subscriber_id))
    subscriber = result.scalar_one_or_none()
    if subscriber is not None:
        subscriber.subscriber_status = status.value
        await session.flush()
    return subscriber
