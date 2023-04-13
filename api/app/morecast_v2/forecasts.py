
from datetime import datetime
from typing import List
from sqlalchemy.orm import Session
from app.db.crud.morecast_v2 import get_forecasts_in_range
from app.schemas.morecast_v2 import MoreCastForecastOutput, WeatherIndeterminate


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
