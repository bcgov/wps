import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from geoalchemy2.shape import to_shape
from wps_shared.auth import authentication_required
from wps_shared.db.crud.smurfi import (
    create_spot_descriptive_weather,
    create_spot_forecast,
    create_spot_request,
    create_spot_tabular_weather,
    get_spot_requests_for_year,
    sync_spot_subscribers,
    update_spot_descriptive_weather,
    update_spot_forecast,
    update_spot_request,
    update_spot_subscriber_status,
    update_spot_tabular_weather,
)
from wps_shared.db.database import get_async_read_session_scope, get_async_write_session_scope
from wps_shared.db.models.smurfi import (
    SpotDescriptiveWeather,
    SpotForecast,
    SpotRequest,
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
    SpotForecastResponse,
    SpotRequestData,
    SpotRequestListResponse,
    SpotRequestResponse,
    SpotRequestUpsertData,
    SpotSubscriberData,
    SpotTabularWeatherData,
    UpdateSubscriberStatusData,
)
from wps_shared.utils.s3_client import S3Client
from wps_shared.utils.time import get_utc_now

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/smurfi", dependencies=[Depends(authentication_required)])


@router.post("/spot_request", response_model=SpotRequestResponse)
async def upsert_spot_request(
    data: SpotRequestUpsertData, token: Annotated[dict, Depends(authentication_required)]
):
    requestor_idir = token.get("idir_username")
    requestor_email = token.get("email")
    first_name = token.get("given_name")
    last_name = token.get("family_name")
    requestor_name = f"{first_name} {last_name}" if first_name and last_name else requestor_idir

    x, y = PointTransformer(
        SpatialReferenceSystem.WGS84.code, NAD83_BC_ALBERS
    ).transform_coordinate(data.latitude, data.longitude)
    now = get_utc_now()

    spot_request = SpotRequest(
        id=data.id,
        request_reference=data.request_reference,
        fire_number=data.fire_number,
        fire_centre=data.fire_centre,
        status=data.status,
        requestor_name=requestor_name,
        requestor_idir=requestor_idir,
        requestor_email=requestor_email,
        request_frequency=data.request_frequency,
        request_type=data.request_type,
        aspect=data.aspect,
        elevation=data.elevation,
        geographic_description=data.geographic_description,
        additional_information=data.additional_information,
        geom=f"POINT({x} {y})",
        requested_at=data.requested_at,
        start_at=data.start_at,
        end_at=data.end_at,
        created_at=now,
        updated_at=now,
    )
    async with get_async_write_session_scope() as session:
        if data.id is None:
            logger.info("Creating a new SpotRequest.")
            result = await create_spot_request(session, spot_request)
        else:
            logger.info("Updating an existing SpotRequest with id: %s.", data.id)
            result = await update_spot_request(session, spot_request)
            if result is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail=f"SpotRequest {data.id} not found"
                )
        logger.info("Syncing subscribers for SpotRequest id: %s", result.id)
        subscribers = await sync_spot_subscribers(
            session, result.id, [s.email for s in data.subscribers]
        )
        spot_request_id = result.id
        subscriber_data = [
            SpotSubscriberData(id=s.id, email=s.email, subscriber_status=s.subscriber_status)
            for s in subscribers
        ]
    spot_request_response = SpotRequestData(
        **data.model_dump(),
        requestor_name=requestor_name,
        requestor_idir=requestor_idir,
        requestor_email=requestor_email,
    )
    return SpotRequestResponse(
        spot_request=spot_request_response.model_copy(
            update={"id": spot_request_id, "subscribers": subscriber_data}
        )
    )


async def _upsert_descriptive_weather(
    session, spot_forecast_id: int, data: SpotForecastData
) -> list[SpotDescriptiveWeatherData]:
    records = []
    for dw in data.descriptive_weather:
        record = SpotDescriptiveWeather(
            id=dw.id,
            spot_forecast_id=spot_forecast_id,
            period=dw.period,
            temperature=dw.temperature,
            relative_humidity=dw.relative_humidity,
            conditions=dw.conditions,
        )
        if dw.id is None:
            logger.info(
                "Creating a new SpotDescriptiveWeather for SpotForecast with id: %s.",
                spot_forecast_id,
            )
            saved = await create_spot_descriptive_weather(session, record)
        else:
            logger.info(
                "Updating existing SpotDescriptiveWeather for SpotForecast with id: %s.",
                spot_forecast_id,
            )
            saved = await update_spot_descriptive_weather(session, record)
            if saved is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"SpotDescriptiveWeather {dw.id} not found",
                )
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


async def _upsert_tabular_weather(
    session, spot_forecast_id: int, data: SpotForecastData
) -> list[SpotTabularWeatherData]:
    records = []
    for tw in data.tabular_weather:
        record = SpotTabularWeather(
            id=tw.id,
            spot_forecast_id=spot_forecast_id,
            forecast_time=tw.forecast_time,
            temperature=tw.temperature,
            relative_humidity=tw.relative_humidity,
            wind=tw.wind,
            probability_of_precipitation=tw.probability_of_precipitation,
            precipitation_amount=tw.precipitation_amount,
        )
        if tw.id is None:
            logger.info(
                "Creating a new SpotTabularWeather for SpotForecast with id: %s.", spot_forecast_id
            )
            saved = await create_spot_tabular_weather(session, record)
        else:
            logger.info(
                "Updating existing SpotTabularWeather for SpotForecast with id: %s.",
                spot_forecast_id,
            )
            saved = await update_spot_tabular_weather(session, record)
            if saved is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"SpotTabularWeather {tw.id} not found",
                )
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
async def upsert_spot_forecast(data: SpotForecastData):
    now = get_utc_now()
    spot_forecast = SpotForecast(
        id=data.id,
        spot_request_id=data.spot_request_id,
        forecaster_name=data.forecaster_name,
        forecaster_email=data.forecaster_email,
        forecaster_phone=data.forecaster_phone,
        synopsis=data.synopsis,
        inversion_and_venting=data.inversion_and_venting,
        outlook=data.outlook,
        confidence=data.confidence,
        fire_size=data.fire_size,
        representative_station_codes=data.representative_station_codes,
        for_date=data.for_date,
        created_at=now,
        updated_at=now,
    )
    async with get_async_write_session_scope() as session:
        if data.id is None:
            logger.info("Creating a new SpotForecast.")
            result = await create_spot_forecast(session, spot_forecast)
        else:
            logger.info("Updaing an existing SpotForecast with id: %s.", data.id)
            result = await update_spot_forecast(session, spot_forecast)
            if result is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"SpotForecast {data.id} not found",
                )
        descriptive_weather = await _upsert_descriptive_weather(session, result.id, data)
        tabular_weather = await _upsert_tabular_weather(session, result.id, data)
    return SpotForecastResponse(
        spot_forecast=data.model_copy(
            update={
                "id": result.id,
                "descriptive_weather": descriptive_weather,
                "tabular_weather": tabular_weather,
            }
        )
    )


def _spot_request_to_schema(spot_request: SpotRequest) -> SpotRequestData:
    shape = to_shape(spot_request.geom)
    lat, lon = PointTransformer(
        NAD83_BC_ALBERS, SpatialReferenceSystem.WGS84.code
    ).transform_coordinate(shape.x, shape.y)
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
        aspect=spot_request.aspect,
        elevation=spot_request.elevation,
        geographic_description=spot_request.geographic_description,
        additional_information=spot_request.additional_information,
        latitude=lat,
        longitude=lon,
        requested_at=spot_request.requested_at,
        start_at=spot_request.start_at,
        end_at=spot_request.end_at,
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
async def get_spot_requests(year: int):
    logger.info("Getting SpotRequests for year: %s", year)
    async with get_async_read_session_scope() as session:
        spot_requests = await get_spot_requests_for_year(session, year)
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
