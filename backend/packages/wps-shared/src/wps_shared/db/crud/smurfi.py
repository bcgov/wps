from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from wps_shared.db.models.smurfi import (
    SpotDescriptiveWeather,
    SpotForecast,
    SpotRequestBase,
    SpotRequestInstance,
    SpotRequestStatusEnum,
    SpotSubscriber,
    SpotSubscriberStatusEnum,
    SpotTabularWeather,
)


async def create_spot_request(session: AsyncSession, spot_request: SpotRequestBase):
    session.add(spot_request)
    await session.flush()
    return spot_request


async def upsert_spot_request(session: AsyncSession, spot_request: SpotRequestBase):
    if spot_request.id is None:
        return await create_spot_request(session, spot_request)
    return await update_spot_request(session, spot_request)


async def create_spot_request_instance(
    session: AsyncSession, spot_request_instance: SpotRequestInstance
) -> SpotRequestInstance:
    session.add(spot_request_instance)
    await session.flush()
    return spot_request_instance


async def get_matching_spot_request_instance(
    session: AsyncSession, spot_request_instance: SpotRequestInstance
) -> SpotRequestInstance | None:
    result = await session.execute(
        select(SpotRequestInstance).where(
            SpotRequestInstance.spot_request_base_id == spot_request_instance.spot_request_base_id,
            SpotRequestInstance.latitude == spot_request_instance.latitude,
            SpotRequestInstance.longitude == spot_request_instance.longitude,
            SpotRequestInstance.geographic_description
            == spot_request_instance.geographic_description,
            SpotRequestInstance.aspect == spot_request_instance.aspect,
            SpotRequestInstance.elevation == spot_request_instance.elevation,
            SpotRequestInstance.valley == spot_request_instance.valley,
        )
    )
    return result.scalar_one_or_none()


async def get_or_create_spot_request_instance(
    session: AsyncSession, spot_request_instance: SpotRequestInstance
) -> SpotRequestInstance:
    existing = await get_matching_spot_request_instance(session, spot_request_instance)
    if existing is not None:
        return existing
    return await create_spot_request_instance(session, spot_request_instance)


async def create_spot_forecast(session: AsyncSession, spot_forecast: SpotForecast):
    session.add(spot_forecast)
    await session.flush()
    return spot_forecast


async def sync_spot_subscribers(
    session: AsyncSession, spot_request_base_id: int, emails: list[str]
) -> list[SpotSubscriber]:
    result = await session.execute(
        select(SpotSubscriber).where(SpotSubscriber.spot_request_base_id == spot_request_base_id)
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
            new_subscriber = SpotSubscriber(spot_request_base_id=spot_request_base_id, email=email)
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


async def start_requested_spot_request(session: AsyncSession, spot_request_base_id: int):
    await session.execute(
        update(SpotRequestBase)
        .where(
            SpotRequestBase.id == spot_request_base_id,
            SpotRequestBase.status == SpotRequestStatusEnum.REQUESTED.value,
        )
        .values(status=SpotRequestStatusEnum.STARTED.value)
    )
    await session.flush()


async def update_spot_request(session: AsyncSession, updated: SpotRequestBase):
    result = await session.execute(select(SpotRequestBase).where(SpotRequestBase.id == updated.id))
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
        existing.additional_information = updated.additional_information
        existing.requested_at = updated.requested_at
        existing.start_at = updated.start_at
        existing.end_at = updated.end_at
        await session.flush()
    return existing


async def get_spot_requests_for_year(session: AsyncSession, year: int):
    year_start = datetime(year, 1, 1, tzinfo=timezone.utc)
    year_end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    result = await session.execute(
        select(SpotRequestBase)
        .where(SpotRequestBase.start_at >= year_start, SpotRequestBase.start_at < year_end)
        .options(
            selectinload(SpotRequestBase.spot_subscribers),
            selectinload(SpotRequestBase.spot_request_instances),
            selectinload(SpotRequestBase.spot_forecasts).selectinload(SpotForecast.tabular_weather),
            selectinload(SpotRequestBase.spot_forecasts).selectinload(
                SpotForecast.spot_request_instance
            ),
        )
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


async def subscribe_to_spot_request(
    session: AsyncSession, spot_request_base_id: int, email: str
) -> SpotSubscriber:
    result = await session.execute(
        select(SpotSubscriber).where(
            SpotSubscriber.spot_request_base_id == spot_request_base_id,
            SpotSubscriber.email == email,
        )
    )
    subscriber = result.scalar_one_or_none()
    if subscriber is None:
        subscriber = SpotSubscriber(
            spot_request_base_id=spot_request_base_id,
            email=email,
            subscriber_status=SpotSubscriberStatusEnum.ACTIVE.value,
        )
        session.add(subscriber)
    else:
        subscriber.subscriber_status = SpotSubscriberStatusEnum.ACTIVE.value
    await session.flush()
    return subscriber


async def unsubscribe_from_spot_request(
    session: AsyncSession, spot_request_base_id: int, email: str
) -> SpotSubscriber | None:
    result = await session.execute(
        select(SpotSubscriber).where(
            SpotSubscriber.spot_request_base_id == spot_request_base_id,
            SpotSubscriber.email == email,
        )
    )
    subscriber = result.scalar_one_or_none()
    if subscriber is not None:
        subscriber.subscriber_status = SpotSubscriberStatusEnum.INACTIVE.value
        await session.flush()
    return subscriber


async def get_subscribed_spot_request_ids(session: AsyncSession, email: str) -> list[int]:
    result = await session.execute(
        select(SpotSubscriber.spot_request_base_id).where(
            SpotSubscriber.email == email,
            SpotSubscriber.subscriber_status == SpotSubscriberStatusEnum.ACTIVE.value,
        )
    )
    return list(result.scalars().all())


async def get_active_subscribers_for_spot(
    session: AsyncSession, spot_request_base_id: int
) -> list[SpotSubscriber]:
    result = await session.execute(
        select(SpotSubscriber).where(
            SpotSubscriber.spot_request_base_id == spot_request_base_id,
            SpotSubscriber.subscriber_status == SpotSubscriberStatusEnum.ACTIVE.value,
        )
    )
    return list(result.scalars().all())


async def get_spot_forecast_with_weather(
    session: AsyncSession, spot_forecast_id: int
) -> SpotForecast | None:
    result = await session.execute(
        select(SpotForecast)
        .where(SpotForecast.id == spot_forecast_id)
        .options(
            selectinload(SpotForecast.descriptive_weather),
            selectinload(SpotForecast.tabular_weather),
            selectinload(SpotForecast.spot_request_base),
            selectinload(SpotForecast.spot_request_instance),
        )
    )
    return result.scalar_one_or_none()


async def get_spot_forecasts_for_request(
    session: AsyncSession, spot_request_base_id: int
) -> list[SpotForecast]:
    result = await session.execute(
        select(SpotForecast)
        .where(SpotForecast.spot_request_base_id == spot_request_base_id)
        .options(
            selectinload(SpotForecast.descriptive_weather),
            selectinload(SpotForecast.tabular_weather),
            selectinload(SpotForecast.spot_request_instance),
        )
        .order_by(SpotForecast.created_at.desc())
    )
    return list(result.scalars().all())
