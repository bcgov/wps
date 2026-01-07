"""Parsers that extract fields from WFWX API responses and build ours"""

import logging
from typing import List

from wps_wf1.models import (
    WeatherDeterminate,
    WeatherIndeterminate,
    WFWXWeatherStation,
)

from wps_shared.schemas.morecast_v2 import MoreCastForecastOutput

logger = logging.getLogger(__name__)


def transform_morecastforecastoutput_to_weatherindeterminate(
    forecast_outputs: List[MoreCastForecastOutput], wfwx_stations: List[WFWXWeatherStation]
) -> List[WeatherIndeterminate]:
    """Helper function to convert list of MoreCastForecastOutput objects (taken from our database)
    into list of WeatherIndeterminate objects to match the structure of the forecasts pulled from WFWX.
    wfwx_stations list (station data from WFWX) is used to populate station_name data.
    """
    weather_indeterminates: List[WeatherIndeterminate] = []
    for output in forecast_outputs:
        station = next(s for s in wfwx_stations if s.code == output.station_code)

        weather_indeterminates.append(
            WeatherIndeterminate(
                station_code=output.station_code,
                station_name=station.name if station else "",
                utc_timestamp=output.for_date,
                determinate=WeatherDeterminate.FORECAST,
                temperature=output.temp,
                relative_humidity=output.rh,
                precipitation=output.precip,
                wind_direction=output.wind_direction,
                wind_speed=output.wind_speed,
            )
        )
    return weather_indeterminates
