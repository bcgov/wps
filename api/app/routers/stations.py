""" Routers for stations """
import logging
from datetime import datetime
from fastapi import APIRouter, Response, Depends
from app.auth import authentication_required, audit
from app.time_utils import get_utc_now
from app.schemas.stations import WeatherStationsResponse, DetailedWeatherStationsResponse
from app.stations import StationSourceEnum, get_stations_as_geojson, fetch_detailed_stations_as_geojson


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/stations",
)


@router.get('/details/', response_model=DetailedWeatherStationsResponse)
async def get_detailed_stations(response: Response,
                                time_of_interest: datetime = None,
                                source: StationSourceEnum = StationSourceEnum.Unspecified,
                                __=Depends(audit),
                                _=Depends(authentication_required)):
    """ Returns a list of fire weather stations with detailed information.
    -) Unspecified: Use configuration to establish source.
    -) LocalStorage: Read from json file  (ignore configuration).
    -) WildfireOne: Use wildfire API (ignore configuration).
    """
    try:
        logger.info('/stations/details/')
        response.headers["Cache-Control"] = "max-age=0"  # don't let the browser cache this
        if time_of_interest is None:
            # NOTE: Don't be tempted to move this into the function definition. It's not possible
            # to mock a function if it's part of the function definition, and will cause
            # tests to fail.
            time_of_interest = get_utc_now()
        weather_stations = await fetch_detailed_stations_as_geojson(time_of_interest, source)

        return DetailedWeatherStationsResponse(features=weather_stations)

    except Exception as exception:
        logger.critical(exception, exc_info=True)
        raise


@router.get('/', response_model=WeatherStationsResponse)
async def get_stations(response: Response,
                       source: StationSourceEnum = StationSourceEnum.Unspecified):
    """ Return a list of fire weather stations.
    Stations source can be:
    -) Unspecified: Use configuration to establish source.
    -) LocalStorage: Read from json file  (ignore configuration).
    -) WildfireOne: Use wildfire API (ignore configuration).
    """
    try:
        logger.info('/stations/')

        weather_stations = await get_stations_as_geojson(source)
        response.headers["Cache-Control"] = "max-age=43200"  # let browsers to cache the data for 12 hours

        return WeatherStationsResponse(features=weather_stations)
    except Exception as exception:
        logger.critical(exception, exc_info=True)
        raise
