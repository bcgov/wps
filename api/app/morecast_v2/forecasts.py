
from datetime import datetime, timezone
from typing import List
from fastapi import Depends, HTTPException, status, Request
from aiohttp.client import ClientSession
from sqlalchemy.orm import Session
from app.auth import authenticate
from app.db.crud.morecast_v2 import get_forecasts_in_range
from app.schemas.morecast_v2 import MoreCastForecastOutput, WeatherIndeterminate, WildfireOneForecastRequest
from app.utils.time import get_utc_now


def get_forecasts(db_session: Session, start_time: datetime, end_time: datetime, station_codes: List[int]) -> List[MoreCastForecastOutput]:
    result = get_forecasts_in_range(db_session, start_time, end_time, station_codes)

    forecasts: List[WeatherIndeterminate] = [MoreCastForecastOutput(station_code=forecast.station_code,
                                                                    for_date=forecast.for_date.timestamp() * 1000,
                                                                    temp=forecast.temp,
                                                                    rh=forecast.rh,
                                                                    precip=forecast.precip,
                                                                    wind_speed=forecast.wind_speed,
                                                                    wind_direction=forecast.wind_direction,
                                                                    update_timestamp=int(forecast.update_timestamp.timestamp())) for forecast in result]
    return forecasts


async def post_forecasts_to_wf1(forecast_data: List[MoreCastForecastOutput], request: Request, token=Depends(authenticate)):
    # format POST body in accordance with WF1 API schema
    wildfire_one_forecast_requests = []
    for forecast in forecast_data:
        wildfire_one_forecast_requests.append(WildfireOneForecastRequest(
            # TODO: need to get station UUID from ... ?
            stationId='1',
            weatherTimestamp=forecast.for_date,
            updateDate=get_utc_now().replace(tzinfo=timezone.utc).timestamp() * 1000,
            # TODO: insert user id strings
            createdBy='',
            lastModifiedBy='',
            temperature=forecast.temp,
            relativeHumidity=forecast.rh,
            windSpeed=forecast.wind_speed,
            windDirection=forecast.wind_direction
        ))

    try:
        async with ClientSession() as session:
