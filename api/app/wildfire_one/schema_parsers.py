""" Parsers that extract fields from WFWX API responses and build ours"""

import math
import logging
from datetime import datetime, timezone
from typing import Generator, List, Optional
from db.models.observations import HourlyActual
from app.schemas.stations import WeatherStation
from app.utils.dewpoint import compute_dewpoint
from app.data.ecodivision_seasons import EcodivisionSeasons
from app.schemas.observations import WeatherReading
from db.models.forecasts import NoonForecast
from app.utils.time import get_utc_now
from app.wildfire_one.util import is_station_valid, is_station_fire_zone_valid, get_zone_code_prefix
from app.wildfire_one.validation import get_valid_flags
from app.schemas.fba import FireCentre, FireCenterStation

logger = logging.getLogger(__name__)


class WFWXWeatherStation():
    """ A WFWX station includes a code and WFWX API specific id """

    def __init__(self,  # pylint: disable=too-many-arguments
                 wfwx_id: str, code: int, latitude: float, longitude: float, elevation: int,
                 name: str, zone_code: Optional[str]):
        self.wfwx_id = wfwx_id
        self.code = code
        self.name = name
        self.lat = latitude
        self.long = longitude
        self.elevation = elevation
        self.zone_code = zone_code


async def station_list_mapper(raw_stations: Generator[dict, None, None]):
    """ Maps raw stations to WeatherStation list"""
    stations = []
    # Iterate through "raw" station data.
    async for raw_station in raw_stations:
        # If the station is valid, add it to our list of stations.
        if is_station_valid(raw_station):
            stations.append(WeatherStation(code=raw_station['stationCode'],
                                           name=raw_station['displayLabel'],
                                           lat=raw_station['latitude'],
                                           long=raw_station['longitude']))
    return stations


async def wfwx_station_list_mapper(raw_stations: Generator[dict, None, None]) -> List[WFWXWeatherStation]:
    """ Maps raw stations to WFWXWeatherStation list"""
    stations = []
    # Iterate through "raw" station data.
    async for raw_station in raw_stations:
        # If the station is valid, add it to our list of stations.
        if is_station_valid(raw_station):
            stations.append(WFWXWeatherStation(wfwx_id=raw_station['id'],
                                               code=raw_station['stationCode'],
                                               latitude=raw_station['latitude'],
                                               longitude=raw_station['longitude'],
                                               elevation=raw_station['elevation'],
                                               name=raw_station['displayLabel'],
                                               zone_code=construct_zone_code(
                                                   raw_station)
                                               ))
    return stations


async def fire_center_mapper(raw_stations: Generator[dict, None, None]):
    """ Maps raw stations to their respective fire centers. """
    fire_centers = {}
    # Iterate through "raw" station data.
    async for raw_station in raw_stations:
        # If the station is valid, add it to our list of stations.
        if is_station_valid(raw_station) and is_station_fire_zone_valid(raw_station):
            raw_fire_center = raw_station['fireCentre']
            fire_center_id = raw_fire_center['id']
            station = FireCenterStation(code=raw_station['stationCode'],
                                        name=raw_station['displayLabel'],
                                        zone=construct_zone_code(raw_station))

            fire_center = fire_centers.get(fire_center_id, None)
            if fire_center is None:
                fire_centers[fire_center_id] = FireCentre(
                    id=raw_fire_center['id'], name=raw_fire_center['displayLabel'], stations=[station])
            else:
                fire_center.stations.append(station)
    return fire_centers


def construct_zone_code(station: any):
    """ Constructs the 2-character zone code for a weather station, using the station's
    zone.alias integer value, prefixed by the fire centre-to-letter mapping.
    """
    if station is None or station['zone'] is None or station['fireCentre'] is None:
        return None
    fire_centre_id = station['fireCentre']['id']
    zone_alias = station['zone']['alias']
    if fire_centre_id is None or zone_alias is None:
        return None
    if get_zone_code_prefix(fire_centre_id) is None:
        return None
    zone_code = get_zone_code_prefix(fire_centre_id) + str(zone_alias)
    return zone_code


def parse_station(station, eco_division: EcodivisionSeasons) -> WeatherStation:
    """ Transform from the json object returned by wf1, to our station object.
    """
    # pylint: disable=no-member
    core_seasons = eco_division.get_core_seasons()
    ecodiv_name = eco_division.get_ecodivision_name(station['stationCode'],
                                                    station['latitude'],
                                                    station['longitude'])
    return WeatherStation(
        zone_code=construct_zone_code(station),
        code=station['stationCode'],
        name=station['displayLabel'],
        lat=station['latitude'],
        long=station['longitude'],
        ecodivision_name=ecodiv_name,
        core_season=core_seasons[ecodiv_name]['core_season'],
        elevation=station['elevation'],
        wfwx_station_uuid=station['id'])


def parse_hourly(hourly) -> WeatherReading:
    """ Transform from the raw hourly json object returned by wf1, to our hourly object.
    """
    timestamp = datetime.fromtimestamp(
        int(hourly['weatherTimestamp']) / 1000, tz=timezone.utc).isoformat()
    return WeatherReading(
        datetime=timestamp,
        temperature=hourly.get('temperature', None),
        relative_humidity=hourly.get('relativeHumidity', None),
        dewpoint=compute_dewpoint(hourly.get(
            'temperature'), hourly.get('relativeHumidity')),
        wind_speed=hourly.get('windSpeed', None),
        wind_direction=hourly.get('windDirection', None),
        barometric_pressure=hourly.get('barometricPressure', None),
        precipitation=hourly.get('precipitation', None),
        ffmc=hourly.get('fineFuelMoistureCode', None),
        isi=hourly.get('initialSpreadIndex', None),
        fwi=hourly.get('fireWeatherIndex', None),
        observation_valid=hourly.get('observationValidInd'),
        observation_valid_comment=hourly.get('observationValidComment')
    )


def parse_noon_forecast(station_code, forecast) -> NoonForecast:
    """ Transform from the raw forecast json object returned by wf1, to our noon forecast object.
    """
    timestamp = datetime.fromtimestamp(
        int(forecast['weatherTimestamp']) / 1000, tz=timezone.utc).isoformat()
    noon_forecast = NoonForecast(
        weather_date=timestamp,
        created_at=get_utc_now(),
        wfwx_update_date=forecast.get('updateDate', None),
        station_code=station_code,
        temperature=forecast.get('temperature', math.nan),
        relative_humidity=forecast.get('relativeHumidity', math.nan),
        wind_speed=forecast.get('windSpeed', math.nan),
        wind_direction=forecast.get('windDirection', math.nan),
        precipitation=forecast.get('precipitation', math.nan),
        gc=forecast.get('grasslandCuring', math.nan),
        ffmc=forecast.get('fineFuelMoistureCode', math.nan),
        dmc=forecast.get('duffMoistureCode', math.nan),
        dc=forecast.get('droughtCode', math.nan),
        isi=forecast.get('initialSpreadIndex', math.nan),
        bui=forecast.get('buildUpIndex', math.nan),
        fwi=forecast.get('fireWeatherIndex', math.nan),
    )
    temp_valid, rh_valid, wdir_valid, wspeed_valid, precip_valid = get_valid_flags(noon_forecast)
    noon_forecast.temp_valid = temp_valid
    noon_forecast.rh_valid = rh_valid
    noon_forecast.wdir_valid = wdir_valid
    noon_forecast.wspeed_valid = wspeed_valid
    noon_forecast.precip_valid = precip_valid
    return noon_forecast


def parse_hourly_actual(station_code: int, hourly):
    """ Transform from the raw hourly json object returned by wf1, to our hour actual object.
    """
    timestamp = datetime.fromtimestamp(
        int(hourly['weatherTimestamp']) / 1000, tz=timezone.utc).isoformat()
    hourly_actual = HourlyActual(
        weather_date=timestamp,
        station_code=station_code,
        temperature=hourly.get('temperature', math.nan),
        relative_humidity=hourly.get('relativeHumidity', math.nan),
        dewpoint=compute_dewpoint(hourly.get(
            'temperature'), hourly.get('relativeHumidity')),
        wind_speed=hourly.get('windSpeed', math.nan),
        wind_direction=hourly.get('windDirection', math.nan),
        precipitation=hourly.get('precipitation', math.nan),
        ffmc=hourly.get('fineFuelMoistureCode', None),
        isi=hourly.get('initialSpreadIndex', None),
        fwi=hourly.get('fireWeatherIndex', None),
    )
    temp_valid, rh_valid, wdir_valid, wspeed_valid, precip_valid = get_valid_flags(hourly_actual)
    hourly_actual.temp_valid = temp_valid
    hourly_actual.rh_valid = rh_valid
    hourly_actual.wdir_valid = wdir_valid
    hourly_actual.wspeed_valid = wspeed_valid
    hourly_actual.precip_valid = precip_valid

    observation_valid = hourly.get('observationValidInd')
    observation_valid_comment = hourly.get('observationValidComment')
    if observation_valid is None or bool(observation_valid) is False:
        logger.warning("Invalid hourly received from WF1 API for station code %s at time %s: %s",
                       station_code,
                       hourly_actual.weather_date,
                       observation_valid_comment)

    is_obs_invalid = not temp_valid and not rh_valid and not wdir_valid\
        and not wspeed_valid and not precip_valid

    if is_obs_invalid:
        logger.error("Hourly actual not written to DB for station code %s at time %s: %s",
                     station_code, hourly_actual.weather_date,
                     observation_valid_comment)

    # don't write the HourlyActual to our database if every value is invalid. If even one
    # weather variable observed is valid, write the HourlyActual to DB.
    return None if is_obs_invalid else hourly_actual
