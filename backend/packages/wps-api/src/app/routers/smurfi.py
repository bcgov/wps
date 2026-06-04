import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from wps_shared.auth import (
    auth_with_forecaster_role_or_spot_owner_required,
    authentication_required,
)
from wps_shared.db.crud.smurfi import (
    COORDINATE_MATCH_TOLERANCE,
    create_distribution_group,
    create_spot_descriptive_weather,
    create_spot_forecast,
    create_spot_request,
    create_spot_request_instance,
    create_spot_tabular_weather,
    delete_distribution_group,
    get_distribution_groups,
    get_or_create_spot_request_instance,
    get_spot_forecasts_for_request,
    get_spot_request_by_id,
    get_spot_requests_for_year,
    get_subscribed_spot_request_ids,
    start_requested_spot_request,
    subscribe_to_spot_request,
    sync_spot_request_distribution_groups,
    sync_spot_subscribers,
    unsubscribe_from_spot_request,
    update_distribution_group,
    update_spot_request_details,
    update_spot_request_instance_details,
    update_spot_request_status,
    update_spot_subscriber_status,
)
from wps_shared.db.database import get_async_read_session_scope, get_async_write_session_scope
from wps_shared.db.models.smurfi import (
    SmurfiDistributionGroup,
    SpotDescriptiveWeather,
    SpotForecast,
    SpotRequestBase,
    SpotRequestInstance,
    SpotRequestStatusEnum,
    SpotSubscriberStatusEnum,
    SpotTabularWeather,
)
from wps_shared.geospatial.geospatial import (
    NAD83_BC_ALBERS,
    PointTransformer,
    SpatialReferenceSystem,
)
from wps_shared.schemas.smurfi import (
    DistributionGroupInput,
    DistributionGroupOutput,
    SpotDescriptiveWeatherData,
    SpotForecastData,
    SpotForecastInput,
    SpotForecastListResponse,
    SpotForecastResponse,
    SpotLatestForecastData,
    SpotRequestData,
    SpotRequestEditInput,
    SpotRequestInput,
    SpotRequestInstanceData,
    SpotRequestInstanceInput,
    SpotRequestListResponse,
    SpotRequestResponse,
    SpotRequestStatusUpdate,
    SpotSubscriberData,
    SpotTabularWeatherData,
    SpotUpdatePayload,
    SubscribeResponse,
    SubscriptionsResponse,
    UpdateSubscriberStatusData,
)
from wps_shared.utils.time import get_utc_now

from app.nats_publish import publish
from app.smurfi.nats_config import smurfi_spot_update_subject, stream_name, subjects

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/smurfi", dependencies=[Depends(authentication_required)])

MISSING_TOKEN_MESSAGE = "Token missing email claim"


@dataclass(frozen=True)
class SpotRequestor:
    name: str
    idir: str
    email: str


def _get_spot_user(token: dict) -> SpotRequestor:
    requestor_idir = token.get("idir_username", None)
    requestor_email = token.get("email", None)
    first_name = token.get("given_name", None)
    last_name = token.get("family_name", None)

    # if either first or last name is missing, use the idir as the name
    requestor_name = " ".join(name for name in [first_name, last_name] if name) or requestor_idir

    return SpotRequestor(name=requestor_name, idir=requestor_idir, email=requestor_email)


def _get_spot_request_subscriber_emails(
    spot_request_input: SpotRequestInput | SpotRequestEditInput, required_emails: list[str]
) -> list[str]:
    seen = set()
    unique_emails = []

    for email in [s.email for s in spot_request_input.subscribers] + required_emails:
        if not email:
            continue

        email = email.strip()
        normalized_email = email.lower()
        if normalized_email not in seen:
            unique_emails.append(email)
            seen.add(normalized_email)

    return unique_emails


def _get_bc_albers_point(latitude: float, longitude: float) -> str:
    x, y = PointTransformer(
        SpatialReferenceSystem.WGS84.code, NAD83_BC_ALBERS
    ).transform_coordinate(latitude, longitude)
    return f"POINT({x} {y})"


def _build_spot_request_base(
    spot_request_input: SpotRequestInput, requestor: SpotRequestor
) -> SpotRequestBase:
    now = get_utc_now()
    return SpotRequestBase(
        **spot_request_input.model_dump(
            exclude={"id", "initial_instance", "subscribers", "distribution_group_ids"}
        ),
        requestor_name=requestor.name,
        requestor_idir=requestor.idir,
        requestor_email=requestor.email,
        created_at=now,
        updated_at=now,
    )


def _build_spot_request_update(
    spot_request_base_id: int, spot_request_input: SpotRequestEditInput
) -> SpotRequestBase:
    return SpotRequestBase(
        id=spot_request_base_id,
        **spot_request_input.model_dump(
            exclude={"request_instance", "subscribers", "distribution_group_ids"}
        ),
    )


def _build_spot_request_instance(
    spot_request_base_id: int, spot_request_instance_input: SpotRequestInstanceInput
) -> SpotRequestInstance:
    return SpotRequestInstance(
        **spot_request_instance_input.model_dump(),
        spot_request_base_id=spot_request_base_id,
        geom=_get_bc_albers_point(
            spot_request_instance_input.latitude, spot_request_instance_input.longitude
        ),
    )


def _spot_request_instance_to_schema(
    spot_request_instance: SpotRequestInstance,
) -> SpotRequestInstanceData:
    return SpotRequestInstanceData(
        id=spot_request_instance.id,
        geographic_description=spot_request_instance.geographic_description,
        aspect=spot_request_instance.aspect,
        elevation=spot_request_instance.elevation,
        valley=spot_request_instance.valley,
        latitude=spot_request_instance.latitude,
        longitude=spot_request_instance.longitude,
        created_at=spot_request_instance.created_at,
    )


def _get_initial_instance(spot_request: SpotRequestBase) -> SpotRequestInstance:
    return min(spot_request.spot_request_instances, key=lambda instance: instance.created_at)


def _get_request_instance(spot_request: SpotRequestBase) -> SpotRequestInstance:
    return _get_initial_instance(spot_request)


def _get_latest_forecast(spot_request: SpotRequestBase) -> SpotForecast | None:
    return max(
        spot_request.spot_forecasts,
        key=lambda forecast: forecast.created_at,
        default=None,
    )


def _coordinate_has_changed(existing: float, updated: float) -> bool:
    return abs(existing - updated) > COORDINATE_MATCH_TOLERANCE


def _spot_request_instance_has_changed(
    existing: SpotRequestInstance, updated: SpotRequestInstanceInput
) -> bool:
    return (
        existing.geographic_description != updated.geographic_description
        or existing.aspect != updated.aspect
        or existing.elevation != updated.elevation
        or existing.valley != updated.valley
        or _coordinate_has_changed(existing.latitude, updated.latitude)
        or _coordinate_has_changed(existing.longitude, updated.longitude)
    )


def _latest_forecast_to_schema(spot_request_base: SpotRequestBase) -> SpotLatestForecastData | None:
    latest_forecast = _get_latest_forecast(spot_request_base)
    if latest_forecast is None:
        return None

    forecast_end_at = max(
        (weather.forecast_time for weather in latest_forecast.tabular_weather),
        default=None,
    )
    return SpotLatestForecastData(
        id=latest_forecast.id,
        created_at=latest_forecast.created_at,
        issued_at=latest_forecast.issued_at,
        expires_at=latest_forecast.expires_at,
        forecast_end_at=forecast_end_at,
        forecaster_name=latest_forecast.forecaster_name,
    )


@router.post("/spot_request", response_model=SpotRequestResponse)
async def create_spot_request_endpoint(
    spot_request_input: SpotRequestInput, token: Annotated[dict, Depends(authentication_required)]
):
    if spot_request_input.id is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Use PATCH /spot_requests/{spot_request_id} to edit a spot request",
        )

    requestor = _get_spot_user(token)
    spot_request_base = _build_spot_request_base(spot_request_input, requestor)

    async with get_async_write_session_scope() as session:
        logger.info("Creating a new SpotRequestBase.")
        result = await create_spot_request(session, spot_request_base)
        # creation always creates the request's editable location instance
        await create_spot_request_instance(
            session, _build_spot_request_instance(result.id, spot_request_input.initial_instance)
        )

        logger.info("Syncing subscribers for SpotRequestBase id: %s", result.id)
        await sync_spot_subscribers(
            session,
            result.id,
            _get_spot_request_subscriber_emails(spot_request_input, [requestor.email]),
        )
        await sync_spot_request_distribution_groups(
            session, result.id, spot_request_input.distribution_group_ids or []
        )
        saved_spot_request = await get_spot_request_by_id(session, result.id)
        if saved_spot_request is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"SpotRequestBase {result.id} not found",
            )
        spot_request = _spot_request_to_schema(saved_spot_request)

    return SpotRequestResponse(spot_request=spot_request)


@router.patch("/spot_requests/{spot_request_id}", response_model=SpotRequestResponse)
async def update_spot_request_endpoint(
    spot_request_id: int,
    spot_request_input: SpotRequestEditInput,
    token: Annotated[dict, Depends(authentication_required)],
):
    async with get_async_write_session_scope() as session:
        existing_spot_request = await get_spot_request_by_id(session, spot_request_id)
        if existing_spot_request is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"SpotRequestBase {spot_request_id} not found",
            )

        result = await update_spot_request_details(
            session, _build_spot_request_update(spot_request_id, spot_request_input)
        )
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"SpotRequestBase {spot_request_id} not found",
            )

        request_instance = _get_request_instance(existing_spot_request)
        # edits update the original request location; forecast locations remain immutable
        if _spot_request_instance_has_changed(
            request_instance, spot_request_input.request_instance
        ):
            await update_spot_request_instance_details(
                session,
                request_instance,
                _build_spot_request_instance(spot_request_id, spot_request_input.request_instance),
            )

        logger.info("Syncing subscribers for SpotRequestBase id: %s", result.id)
        await sync_spot_subscribers(
            session,
            result.id,
            _get_spot_request_subscriber_emails(
                spot_request_input, [existing_spot_request.requestor_email]
            ),
        )
        await sync_spot_request_distribution_groups(
            session, result.id, spot_request_input.distribution_group_ids or []
        )
        saved_spot_request = await get_spot_request_by_id(session, result.id)
        if saved_spot_request is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"SpotRequestBase {spot_request_id} not found",
            )
        spot_request = _spot_request_to_schema(saved_spot_request)

    return SpotRequestResponse(spot_request=spot_request)


async def _create_descriptive_weather(
    session, spot_forecast_id: int, data: SpotForecastInput
) -> list[SpotDescriptiveWeatherData]:
    records = []
    for dw in data.descriptive_weather:
        record = SpotDescriptiveWeather(
            spot_forecast_id=spot_forecast_id,
            period=dw.period,
            temperature=dw.temperature,
            relative_humidity=dw.relative_humidity,
            conditions=dw.conditions,
        )
        logger.info(
            "Creating a new SpotDescriptiveWeather for SpotForecast with id: %s.",
            spot_forecast_id,
        )
        saved = await create_spot_descriptive_weather(session, record)
        records.append(
            SpotDescriptiveWeatherData(
                id=saved.id,
                period=saved.period,
                temperature=saved.temperature,
                relative_humidity=saved.relative_humidity,
                conditions=saved.conditions,
            )
        )
    return records


async def _create_tabular_weather(
    session, spot_forecast_id: int, data: SpotForecastInput
) -> list[SpotTabularWeatherData]:
    records = []
    for tw in data.tabular_weather:
        record = SpotTabularWeather(
            spot_forecast_id=spot_forecast_id,
            forecast_time=tw.forecast_time,
            temperature=tw.temperature,
            relative_humidity=tw.relative_humidity,
            wind=tw.wind,
            probability_of_precipitation=tw.probability_of_precipitation,
            precipitation_amount=tw.precipitation_amount,
        )
        logger.info(
            "Creating a new SpotTabularWeather for SpotForecast with id: %s.", spot_forecast_id
        )
        saved = await create_spot_tabular_weather(session, record)
        records.append(
            SpotTabularWeatherData(
                id=saved.id,
                forecast_time=saved.forecast_time,
                temperature=saved.temperature,
                relative_humidity=saved.relative_humidity,
                wind=saved.wind,
                probability_of_precipitation=saved.probability_of_precipitation,
                precipitation_amount=saved.precipitation_amount,
            )
        )
    return records


@router.post("/spot_forecast", response_model=SpotForecastResponse)
async def create_spot_forecast_endpoint(
    spot_forecast_input: SpotForecastInput, token: Annotated[dict, Depends(authentication_required)]
):
    now = get_utc_now()
    forecaster = _get_spot_user(token)
    if not forecaster.email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=MISSING_TOKEN_MESSAGE)
    async with get_async_write_session_scope() as session:
        # forecasts can reuse an identical location instance; request edits intentionally do not
        spot_request_instance = await get_or_create_spot_request_instance(
            session,
            _build_spot_request_instance(
                spot_forecast_input.spot_request_base_id, spot_forecast_input.spot_request_instance
            ),
        )
        spot_forecast = SpotForecast(
            spot_request_base_id=spot_forecast_input.spot_request_base_id,
            spot_request_instance_id=spot_request_instance.id,
            forecaster_name=forecaster.name,
            forecaster_email=forecaster.email,
            forecaster_phone=None,
            synopsis=spot_forecast_input.synopsis,
            inversion_and_venting=spot_forecast_input.inversion_and_venting,
            outlook=spot_forecast_input.outlook,
            confidence=spot_forecast_input.confidence,
            forecast_type=spot_forecast_input.forecast_type,
            fire_size=spot_forecast_input.fire_size,
            representative_station_codes=spot_forecast_input.representative_station_codes,
            issued_at=spot_forecast_input.issued_at,
            expires_at=spot_forecast_input.expires_at,
            created_at=now,
        )
        logger.info("Creating a new SpotForecast.")
        result = await create_spot_forecast(session, spot_forecast)

        spot_forecast_id = result.id
        descriptive_weather = await _create_descriptive_weather(
            session, spot_forecast_id, spot_forecast_input
        )
        tabular_weather = await _create_tabular_weather(
            session, spot_forecast_id, spot_forecast_input
        )
        await start_requested_spot_request(session, spot_forecast_input.spot_request_base_id)
        spot_request_instance_id = spot_request_instance.id
        spot_request_instance_data = _spot_request_instance_to_schema(spot_request_instance)

    payload = SpotUpdatePayload(
        spot_request_id=spot_forecast_input.spot_request_base_id, spot_forecast_id=spot_forecast_id
    )
    await publish(
        stream=stream_name, subject=smurfi_spot_update_subject, payload=payload, subjects=subjects
    )
    return SpotForecastResponse(
        spot_forecast=SpotForecastData(
            **spot_forecast_input.model_dump(
                exclude={"descriptive_weather", "tabular_weather", "spot_request_instance"}
            ),
            id=spot_forecast_id,
            spot_request_instance_id=spot_request_instance_id,
            spot_request_instance=spot_request_instance_data,
            created_at=now,
            forecaster_name=forecaster.name,
            forecaster_email=forecaster.email,
            forecaster_phone=None,
            descriptive_weather=descriptive_weather,
            tabular_weather=tabular_weather,
        )
    )


def _spot_forecast_to_schema(spot_forecast: SpotForecast) -> SpotForecastData:
    period_order = {"Today": 0, "Tonight": 1, "Tomorrow": 2}
    descriptive_weather = sorted(
        spot_forecast.descriptive_weather, key=lambda item: period_order.get(item.period, 99)
    )
    tabular_weather = sorted(spot_forecast.tabular_weather, key=lambda item: item.forecast_time)

    return SpotForecastData(
        id=spot_forecast.id,
        spot_request_base_id=spot_forecast.spot_request_base_id,
        spot_request_instance_id=spot_forecast.spot_request_instance_id,
        spot_request_instance=_spot_request_instance_to_schema(spot_forecast.spot_request_instance),
        forecaster_name=spot_forecast.forecaster_name,
        forecaster_email=spot_forecast.forecaster_email,
        forecaster_phone=spot_forecast.forecaster_phone,
        synopsis=spot_forecast.synopsis,
        inversion_and_venting=spot_forecast.inversion_and_venting,
        outlook=spot_forecast.outlook,
        confidence=spot_forecast.confidence,
        forecast_type=spot_forecast.forecast_type,
        fire_size=spot_forecast.fire_size,
        representative_station_codes=spot_forecast.representative_station_codes,
        created_at=spot_forecast.created_at,
        issued_at=spot_forecast.issued_at,
        expires_at=spot_forecast.expires_at,
        descriptive_weather=[
            SpotDescriptiveWeatherData(
                id=item.id,
                period=item.period,
                temperature=item.temperature,
                relative_humidity=item.relative_humidity,
                conditions=item.conditions,
            )
            for item in descriptive_weather
        ],
        tabular_weather=[
            SpotTabularWeatherData(
                id=item.id,
                forecast_time=item.forecast_time,
                temperature=item.temperature,
                relative_humidity=item.relative_humidity,
                wind=item.wind,
                probability_of_precipitation=item.probability_of_precipitation,
                precipitation_amount=item.precipitation_amount,
            )
            for item in tabular_weather
        ],
    )


@router.patch("/spot_requests/{spot_request_id}/status", response_model=SpotRequestResponse)
async def update_spot_request_status_endpoint(
    spot_request_id: int,
    data: SpotRequestStatusUpdate,
    _: Annotated[dict, Depends(auth_with_forecaster_role_or_spot_owner_required)],
):
    try:
        next_status = SpotRequestStatusEnum(data.status)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid status: {data.status}"
        )

    # once work has started, requests should not move back to the initial Requested state
    if next_status == SpotRequestStatusEnum.REQUESTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Spot request status cannot be changed back to Requested",
        )

    async with get_async_write_session_scope() as session:
        spot_request = await get_spot_request_by_id(session, spot_request_id)
        if spot_request is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"SpotRequestBase {spot_request_id} not found",
            )

        updated_spot_request = await update_spot_request_status(session, spot_request, next_status)
        spot_request_data = _spot_request_to_schema(updated_spot_request)

    return SpotRequestResponse(spot_request=spot_request_data)


@router.get(
    "/spot_requests/{spot_request_id}/spot_forecasts",
    response_model=SpotForecastListResponse,
)
async def get_spot_forecasts(spot_request_id: int):
    async with get_async_read_session_scope() as session:
        spot_forecasts = await get_spot_forecasts_for_request(session, spot_request_id)
        return SpotForecastListResponse(
            spot_forecasts=[_spot_forecast_to_schema(forecast) for forecast in spot_forecasts]
        )


def _spot_request_to_schema(spot_request: SpotRequestBase) -> SpotRequestData:
    request_instance = _get_request_instance(spot_request)
    return SpotRequestData(
        id=spot_request.id,
        request_reference=spot_request.request_reference,
        fire_number=spot_request.fire_number,
        fire_centre=spot_request.fire_centre,
        status=spot_request.status,
        requestor_name=spot_request.requestor_name,
        requestor_idir=spot_request.requestor_idir,
        requestor_email=spot_request.requestor_email,
        request_frequency=spot_request.request_frequency,
        request_type=spot_request.request_type,
        additional_information=spot_request.additional_information,
        request_instance=_spot_request_instance_to_schema(request_instance),
        requested_at=spot_request.requested_at,
        start_at=spot_request.start_at,
        end_at=spot_request.end_at,
        latest_forecast=_latest_forecast_to_schema(spot_request),
        subscribers=[
            SpotSubscriberData(id=s.id, email=s.email, subscriber_status=s.subscriber_status)
            for s in spot_request.spot_subscribers
            if s.subscriber_status == SpotSubscriberStatusEnum.ACTIVE.value
        ],
        distribution_groups=[
            DistributionGroupOutput.to_schema(g) for g in spot_request.distribution_groups
        ],
        distribution_group_ids=[g.id for g in spot_request.distribution_groups],
    )


@router.post("/update_subscriber", status_code=status.HTTP_204_NO_CONTENT)
async def update_subscriber(data: UpdateSubscriberStatusData):
    try:
        status_enum = SpotSubscriberStatusEnum(data.status)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid status: {data.status}"
        )
    async with get_async_write_session_scope() as session:
        result = await update_spot_subscriber_status(session, data.subscriber_id, status_enum)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscriber {data.subscriber_id} not found",
        )


@router.get("/distribution_groups", response_model=list[DistributionGroupOutput])
async def get_distribution_groups_endpoint(
    token: Annotated[dict, Depends(authentication_required)],
):
    user = _get_spot_user(token)
    async with get_async_read_session_scope() as session:
        groups = await get_distribution_groups(session, user.idir)
    return [DistributionGroupOutput.to_schema(g) for g in groups]


@router.post(
    "/distribution_groups",
    response_model=DistributionGroupOutput,
    status_code=status.HTTP_201_CREATED,
)
async def create_distribution_group_endpoint(
    data: DistributionGroupInput, token: Annotated[dict, Depends(authentication_required)]
):
    user = _get_spot_user(token)
    group = SmurfiDistributionGroup(name=data.name, emails=data.emails, owner_idir=user.idir)
    async with get_async_write_session_scope() as session:
        result = await create_distribution_group(session, group)
        return DistributionGroupOutput.to_schema(result)


@router.put("/distribution_groups/{group_id}", response_model=DistributionGroupOutput)
async def update_distribution_group_endpoint(
    group_id: int,
    data: DistributionGroupInput,
    token: Annotated[dict, Depends(authentication_required)],
):
    user = _get_spot_user(token)
    async with get_async_write_session_scope() as session:
        result = await update_distribution_group(
            session, group_id, data.name, data.emails, user.idir
        )
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Distribution group {group_id} not found",
            )
        return DistributionGroupOutput.to_schema(result)


@router.delete("/distribution_groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_distribution_group_endpoint(
    group_id: int, token: Annotated[dict, Depends(authentication_required)]
):
    user = _get_spot_user(token)
    async with get_async_write_session_scope() as session:
        found = await delete_distribution_group(session, group_id, user.idir)
    if not found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Distribution group {group_id} not found",
        )


@router.get("/spot_requests", response_model=SpotRequestListResponse)
async def get_spot_requests():
    now = datetime.now()
    logger.info("Getting SpotRequests for year: %s", now.year)
    async with get_async_read_session_scope() as session:
        spot_requests = await get_spot_requests_for_year(session, now.year)
    return SpotRequestListResponse(
        spot_requests=[_spot_request_to_schema(sr) for sr in spot_requests]
    )


@router.post("/spots/{spot_request_id}/subscribe", response_model=SubscribeResponse)
async def subscribe_to_spot(
    spot_request_id: int, token: Annotated[dict, Depends(authentication_required)]
):
    email = token.get("email", None)
    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=MISSING_TOKEN_MESSAGE)
    async with get_async_write_session_scope() as session:
        subscriber = await subscribe_to_spot_request(session, spot_request_id, email)
        subscriber_status = subscriber.subscriber_status
    return SubscribeResponse(subscriber_status=subscriber_status)


@router.delete("/spots/{spot_request_id}/subscribe", status_code=status.HTTP_204_NO_CONTENT)
async def unsubscribe_from_spot(
    spot_request_id: int, token: Annotated[dict, Depends(authentication_required)]
):
    email = token.get("email", None)
    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=MISSING_TOKEN_MESSAGE)
    async with get_async_write_session_scope() as session:
        result = await unsubscribe_from_spot_request(session, spot_request_id, email)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription for spot request {spot_request_id} not found",
        )


@router.get("/subscriptions", response_model=SubscriptionsResponse)
async def get_subscriptions(token: Annotated[dict, Depends(authentication_required)]):
    email = token.get("email", None)
    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=MISSING_TOKEN_MESSAGE)
    async with get_async_read_session_scope() as session:
        ids = await get_subscribed_spot_request_ids(session, email)
    return SubscriptionsResponse(spot_request_ids=ids)
