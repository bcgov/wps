import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from wps_shared.auth import authentication_required
from wps_shared.db.crud.smurfi import (
    create_spot_descriptive_weather,
    create_spot_forecast,
    create_spot_request_instance,
    create_spot_tabular_weather,
    get_or_create_spot_request_instance,
    get_spot_forecasts_for_request,
    get_spot_requests_for_year,
    get_subscribed_spot_request_ids,
    start_requested_spot_request,
    subscribe_to_spot_request,
    sync_spot_subscribers,
    unsubscribe_from_spot_request,
    update_spot_subscriber_status,
    upsert_spot_request,
)
from wps_shared.db.database import get_async_read_session_scope, get_async_write_session_scope
from wps_shared.db.models.smurfi import (
    SpotDescriptiveWeather,
    SpotForecast,
    SpotRequestBase,
    SpotRequestInstance,
    SpotSubscriberStatusEnum,
    SpotTabularWeather,
)
from wps_shared.geospatial.geospatial import (
    NAD83_BC_ALBERS,
    PointTransformer,
    SpatialReferenceSystem,
)
from wps_shared.schemas.smurfi import (
    SpotDescriptiveWeatherData,
    SpotForecastData,
    SpotForecastInput,
    SpotForecastListResponse,
    SpotForecastResponse,
    SpotLatestForecastData,
    SpotRequestData,
    SpotRequestInput,
    SpotRequestInstanceData,
    SpotRequestInstanceInput,
    SpotRequestListResponse,
    SpotRequestResponse,
    SpotSubscriberData,
    SpotTabularWeatherData,
    SpotUpdatePayload,
    SubscribeResponse,
    SubscriptionsResponse,
    UpdateSubscriberStatusData,
)
from wps_shared.utils.s3_client import S3Client
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


def _get_bc_albers_point(latitude: float, longitude: float) -> str:
    x, y = PointTransformer(
        SpatialReferenceSystem.WGS84.code, NAD83_BC_ALBERS
    ).transform_coordinate(latitude, longitude)
    return f"POINT({x} {y})"


def _build_spot_request_base(data: SpotRequestInput, requestor: SpotRequestor) -> SpotRequestBase:
    now = get_utc_now()
    return SpotRequestBase(
        **data.model_dump(exclude={"initial_instance", "subscribers"}),
        requestor_name=requestor.name,
        requestor_idir=requestor.idir,
        requestor_email=requestor.email,
        created_at=now,
        updated_at=now,
    )


def _build_spot_request_instance(
    spot_request_base_id: int, data: SpotRequestInstanceInput
) -> SpotRequestInstance:
    return SpotRequestInstance(
        **data.model_dump(),
        spot_request_base_id=spot_request_base_id,
        geom=_get_bc_albers_point(data.latitude, data.longitude),
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
    )


def _get_initial_instance(spot_request: SpotRequestBase) -> SpotRequestInstance:
    return min(spot_request.spot_request_instances, key=lambda instance: instance.created_at)


def _get_latest_forecast(spot_request: SpotRequestBase) -> SpotForecast | None:
    return max(
        spot_request.spot_forecasts,
        key=lambda forecast: forecast.created_at,
        default=None,
    )


def _get_current_instance(spot_request: SpotRequestBase) -> SpotRequestInstance:
    latest_forecast = _get_latest_forecast(spot_request)
    if latest_forecast is not None:
        return latest_forecast.spot_request_instance
    return _get_initial_instance(spot_request)


def _latest_forecast_to_schema(spot_request: SpotRequestBase) -> SpotLatestForecastData | None:
    latest_forecast = _get_latest_forecast(spot_request)
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
async def upsert_spot_request_endpoint(
    data: SpotRequestInput, token: Annotated[dict, Depends(authentication_required)]
):
    requestor = _get_spot_user(token)
    spot_request_base = _build_spot_request_base(data, requestor)

    async with get_async_write_session_scope() as session:
        if spot_request_base.id is None:
            logger.info("Creating a new SpotRequestBase.")
        else:
            logger.info("Updating an existing SpotRequestBase with id: %s.", spot_request_base.id)

        result = await upsert_spot_request(session, spot_request_base)
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"SpotRequestBase {spot_request_base.id} not found",
            )

        initial_instance = await create_spot_request_instance(
            session, _build_spot_request_instance(result.id, data.initial_instance)
        )

        logger.info("Syncing subscribers for SpotRequestBase id: %s", result.id)
        subscribers = await sync_spot_subscribers(
            session, result.id, [s.email for s in data.subscribers]
        )
        spot_request_base_id = result.id
        subscriber_data = [
            SpotSubscriberData(id=s.id, email=s.email, subscriber_status=s.subscriber_status)
            for s in subscribers
        ]
        initial_instance_data = _spot_request_instance_to_schema(initial_instance)

    return SpotRequestResponse(
        spot_request=SpotRequestData(
            **data.model_dump(exclude={"id", "initial_instance", "subscribers"}),
            id=spot_request_base_id,
            initial_instance=initial_instance_data,
            current_instance=initial_instance_data,
            subscribers=subscriber_data,
            requestor_name=requestor.name,
            requestor_idir=requestor.idir,
            requestor_email=requestor.email,
        )
    )


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
    data: SpotForecastInput, token: Annotated[dict, Depends(authentication_required)]
):
    now = get_utc_now()
    forecaster = _get_spot_user(token)
    if not forecaster.email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=MISSING_TOKEN_MESSAGE)
    async with get_async_write_session_scope() as session:
        spot_request_instance = await get_or_create_spot_request_instance(
            session,
            _build_spot_request_instance(data.spot_request_base_id, data.spot_request_instance),
        )
        spot_forecast = SpotForecast(
            spot_request_base_id=data.spot_request_base_id,
            spot_request_instance_id=spot_request_instance.id,
            forecaster_name=forecaster.name,
            forecaster_email=forecaster.email,
            forecaster_phone=None,
            synopsis=data.synopsis,
            inversion_and_venting=data.inversion_and_venting,
            outlook=data.outlook,
            confidence=data.confidence,
            fire_size=data.fire_size,
            representative_station_codes=data.representative_station_codes,
            issued_at=data.issued_at,
            expires_at=data.expires_at,
            created_at=now,
        )
        logger.info("Creating a new SpotForecast.")
        result = await create_spot_forecast(session, spot_forecast)

        spot_forecast_id = result.id
        descriptive_weather = await _create_descriptive_weather(session, spot_forecast_id, data)
        tabular_weather = await _create_tabular_weather(session, spot_forecast_id, data)
        await start_requested_spot_request(session, data.spot_request_base_id)
        spot_request_instance_id = spot_request_instance.id
        spot_request_instance_data = _spot_request_instance_to_schema(spot_request_instance)

    payload = SpotUpdatePayload(
        spot_request_id=data.spot_request_base_id, spot_forecast_id=spot_forecast_id
    )
    await publish(
        stream=stream_name, subject=smurfi_spot_update_subject, payload=payload, subjects=subjects
    )
    return SpotForecastResponse(
        spot_forecast=SpotForecastData(
            **data.model_dump(
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
    initial_instance = _get_initial_instance(spot_request)
    current_instance = _get_current_instance(spot_request)
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
        initial_instance=_spot_request_instance_to_schema(initial_instance),
        current_instance=_spot_request_instance_to_schema(current_instance),
        requested_at=spot_request.requested_at,
        start_at=spot_request.start_at,
        end_at=spot_request.end_at,
        latest_forecast=_latest_forecast_to_schema(spot_request),
        subscribers=[
            SpotSubscriberData(id=s.id, email=s.email, subscriber_status=s.subscriber_status)
            for s in spot_request.spot_subscribers
            if s.subscriber_status == SpotSubscriberStatusEnum.ACTIVE.value
        ],
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


@router.get("/spot_requests", response_model=SpotRequestListResponse)
async def get_spot_requests():
    now = datetime.now()
    logger.info("Getting SpotRequests for year: %s", now.year)
    async with get_async_read_session_scope() as session:
        spot_requests = await get_spot_requests_for_year(session, now.year)
    return SpotRequestListResponse(
        spot_requests=[_spot_request_to_schema(sr) for sr in spot_requests]
    )


@router.get("/pdf/{spot_id}")
async def get_spot_pdf(spot_id: int):
    """Get the PDF for a spot from S3"""
    # Generate the expected S3 key for the PDF
    pdf_key = f"smurfi/{spot_id}.pdf"

    try:
        # Get the PDF from S3 using stream_object
        generator, response = await S3Client.stream_object(pdf_key)

        # Read all chunks into bytes
        pdf_bytes = b""
        async for chunk in generator:
            pdf_bytes += chunk

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"inline; filename=spot_forecast_{spot_id}.pdf"},
        )
    except Exception as e:
        logger.error(f"Failed to get PDF for spot {spot_id}: {e}")
        return Response(status_code=404, content="PDF not found")


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
