""" Parsers that extract fields from WFWX API responses and build ours"""

import math
import logging
from datetime import datetime, timezone
from typing import Generator, List, Optional
from app.db.models.observations import HourlyActual
from app.schemas.morecast_v2 import ObservedDaily, WeatherDeterminate, WeatherIndeterminate
from app.schemas.stations import (WeatherStationGroup, WeatherStation,
                                  WeatherStationGroupMember, FireZone, StationFireCentre)
from app.utils.dewpoint import compute_dewpoint
from app.data.ecodivision_seasons import EcodivisionSeasons
from app.schemas.observations import WeatherReading
from app.db.models.forecasts import NoonForecast
from app.utils.time import get_utc_now
from app.wildfire_one.util import is_station_valid, is_station_fire_zone_valid, get_zone_code_prefix
from app.wildfire_one.validation import get_valid_flags
from app.schemas.fba import FireCentre, FireCenterStation

logger = logging.getLogger(__name__)


class WFWXWeatherStation():
    """ A WFWX station includes a code and WFWX API specific id """

    def __init__(self,
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


async def yesterday_dailies_list_mapper(raw_dailies: Generator[dict, None, None]):
    """ Maps raw dailies to yesterday dailies list"""
    yesterday_dailies = []
    async for raw_daily in raw_dailies:
        if is_station_valid(raw_daily.get('stationData')) and raw_daily.get('recordType').get('id') == "ACTUAL":
            yesterday_dailies.append(ObservedDaily(
                created_by=raw_daily.get('createdBy'),
                forecast_id=raw_daily.get('id'),
                station_code=raw_daily.get('stationData').get('stationCode'),
                station_name=raw_daily.get('stationData').get('displayLabel'),
                utcTimestamp=datetime.fromtimestamp(raw_daily.get('weatherTimestamp') / 1000, tz=timezone.utc),
                temperature=raw_daily.get('temperature'),
                relative_humidity=raw_daily.get('relativeHumidity'),
                precipitation=raw_daily.get('precipitation'),
                wind_direction=raw_daily.get('windDirection'),
                wind_speed=raw_daily.get('windSpeed')
            ))
    return yesterday_dailies


async def forecast_dailies_list_mapper(raw_dailies: Generator[dict, None, None]):
    """ Maps raw dailies to forecast dailies list"""
    forecast_dailies = []
    async for raw_daily in raw_dailies:
        if is_station_valid(raw_daily.get('stationData')) and raw_daily.get('recordType').get('id') == "FORECAST":
            forecast_dailies.append(ObservedDaily(
                created_by=raw_daily.get('createdBy'),
                forecast_id=raw_daily.get('id'),
                station_code=raw_daily.get('stationData').get('stationCode'),
                station_name=raw_daily.get('stationData').get('displayLabel'),
                utcTimestamp=datetime.fromtimestamp(raw_daily.get('weatherTimestamp') / 1000, tz=timezone.utc),
                temperature=raw_daily.get('temperature'),
                relative_humidity=raw_daily.get('relativeHumidity'),
                precipitation=raw_daily.get('precipitation'),
                wind_direction=raw_daily.get('windDirection'),
                wind_speed=raw_daily.get('windSpeed')
            ))
    return forecast_dailies


async def weather_indeterminate_list_mapper(raw_dailies: Generator[dict, None, None]):
    """ Maps raw dailies to weather indeterminate list"""
    observed_dailies = []
    forecasts = []
    async for raw_daily in raw_dailies:
        if is_station_valid(raw_daily.get('stationData')) and raw_daily.get('recordType').get('id') == "ACTUAL":
            observed_dailies.append(WeatherIndeterminate(
                station_code=raw_daily.get('stationData').get('stationCode'),
                station_name=raw_daily.get('stationData').get('displayLabel'),
                determinate=WeatherDeterminate.ACTUAL,
                utc_timestamp=datetime.fromtimestamp(raw_daily.get('weatherTimestamp') / 1000, tz=timezone.utc),
                temperature=raw_daily.get('temperature'),
                relative_humidity=raw_daily.get('relativeHumidity'),
                precipitation=raw_daily.get('precipitation'),
                wind_direction=raw_daily.get('windDirection'),
                wind_speed=raw_daily.get('windSpeed')
            ))
        elif is_station_valid(raw_daily.get('stationData')) and raw_daily.get('recordType').get('id') == "FORECAST":
            forecasts.append(WeatherIndeterminate(
                station_code=raw_daily.get('stationData').get('stationCode'),
                station_name=raw_daily.get('stationData').get('displayLabel'),
                determinate=WeatherDeterminate.FORECAST,
                utc_timestamp=datetime.fromtimestamp(raw_daily.get('weatherTimestamp') / 1000, tz=timezone.utc),
                temperature=raw_daily.get('temperature'),
                relative_humidity=raw_daily.get('relativeHumidity'),
                precipitation=raw_daily.get('precipitation'),
                wind_direction=raw_daily.get('windDirection'),
                wind_speed=raw_daily.get('windSpeed')
            ))
    return observed_dailies, forecasts


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


async def weather_station_group_mapper(raw_station_groups_by_owner: Generator[dict, None, None]) -> List[WeatherStationGroup]:
    """ Maps raw weather station groups to WeatherStationGroup"""
    weather_station_groups = []
    async for raw_group in raw_station_groups_by_owner:
        weather_station_groups.append(WeatherStationGroup(
            display_label=raw_group['displayLabel'],
            group_description=raw_group['groupDescription'],
            group_owner_user_guid=raw_group['groupOwnerUserGuid'],
            group_owner_user_id=raw_group['groupOwnerUserId'],
            id=raw_group['id']))

    return weather_station_groups


def weather_stations_mapper(stations) -> List[WeatherStationGroupMember]:
    mapped_stations = []
    for item in stations:
        station = item['station']
        fire_zone = FireZone(id=station['zone']['id'], display_label=station['zone']['displayLabel'],
                             fire_centre=station['zone']['fireCentre']) if station['zone'] is not None else None
        weather_station = WeatherStationGroupMember(
            id=station['id'],
            display_label=station['displayLabel'],
            fire_centre=StationFireCentre(id=station['fireCentre']['id'],
                                          display_label=station['fireCentre']['displayLabel']),
            fire_zone=fire_zone,
            station_code=station['stationCode'],
            station_status=station['stationStatus']['id']
        )
        mapped_stations.append(weather_station)

    return mapped_stations


def unique_weather_stations_mapper(stations) -> List[WeatherStationGroupMember]:
    all_stations = weather_stations_mapper(stations)
    unique_stations = []
    stations_added = set()

    for station in all_stations:
        if station.station_code not in stations_added:
            unique_stations.append(station)
            stations_added.add(station.station_code)

    return unique_stations
