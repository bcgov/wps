""" Parsers that extract fields from WFWX API responses and build ours"""

import math
import logging
from datetime import datetime, timezone
from typing import Generator, List
from app.db.models.observations import HourlyActual
from app.schemas.fba_calc import StationResponse
from app.schemas.stations import WeatherStation
from app.utils.cffdrs import crown_fraction_burned, foliar_moisture_content, head_fire_intensity, length_to_breadth_ratio, rate_of_spread, surface_fuel_consumption
from app.utils.dewpoint import compute_dewpoint
from app.data.ecodivision_seasons import EcodivisionSeasons
from app.schemas.observations import WeatherReading
from app.schemas.hfi_calc import StationDaily
from app.utils.fba_calculator import FBACalculatorWeatherStation, get_30_minutes_fire_size, get_60_minutes_fire_size, get_approx_flame_length, get_fire_type
from app.utils.time import get_julian_date, get_julian_date_now, get_hour_20_from_date
from app.wildfire_one.util import is_station_valid

logger = logging.getLogger(__name__)


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


class WFWXWeatherStation():
    """ A WFWX station includes a code and WFWX API specific id """

    def __init__(self, wfwx_id: str, code: int, latitude: float, longitude: float, elevation: int):
        self.wfwx_id = wfwx_id
        self.code = code
        self.lat = latitude
        self.long = longitude
        self.elevation = elevation


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
                                               elevation=raw_station['elevation']
                                               ))
    return stations


def parse_station(station) -> WeatherStation:
    """ Transform from the json object returned by wf1, to our station object.
    """
    # pylint: disable=no-member
    core_seasons = EcodivisionSeasons.instance().get_core_seasons()
    ecodiv_name = EcodivisionSeasons.instance().get_ecodivision_name(
        station['stationCode'], station['latitude'], station['longitude'])
    return WeatherStation(
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
        int(hourly['weatherTimestamp'])/1000, tz=timezone.utc).isoformat()
    return WeatherReading(
        datetime=timestamp,
        temperature=hourly.get('temperature', None),
        relative_humidity=hourly.get('relativeHumidity', None),
        dewpoint=compute_dewpoint(hourly.get('temperature'), hourly.get('relativeHumidity')),
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


def parse_to_StationDaily(raw_daily, station: WFWXWeatherStation, fuel_type: str) -> StationDaily:
    """ Transform from the raw daily json object returned by wf1, to our daily object.
    """

    isi = raw_daily.get('initialSpreadIndex', None)
    bui = raw_daily.get('buildUpIndex', None)
    ffmc = raw_daily.get('fineFuelMoistureCode', None)
    fmc = foliar_moisture_content(station.lat, station.long, station.elevation, get_julian_date_now())
    sfc = surface_fuel_consumption(fuel_type, bui, ffmc, None)
    ros = rate_of_spread(fuel_type, isi, bui, fmc, sfc, None, raw_daily.get('grasslandCuring', None))
    return StationDaily(
        code=station.code,
        status="Observed" if raw_daily.get('recordType', '').get('id') == 'ACTUAL' else "Forecasted",
        temperature=raw_daily.get('temperature', None),
        relative_humidity=raw_daily.get('relativeHumidity', None),
        wind_speed=raw_daily.get('windSpeed', None),
        wind_direction=raw_daily.get('windDirection', None),
        precipitation=raw_daily.get('precipitation', None),
        grass_cure_percentage=raw_daily.get('grasslandCuring', None),
        ffmc=ffmc,
        dmc=raw_daily.get('duffMoistureCode', None),
        dc=raw_daily.get('droughtCode', None),
        fwi=raw_daily.get('fireWeatherIndex', None),
        danger_class=raw_daily.get('dailySeverityRating', None),
        isi=isi,
        bui=bui,
        rate_of_spread=ros,
        observation_valid=raw_daily.get('observationValidInd', None),
        observation_valid_comment=raw_daily.get('observationValidComment', None)
    )


def parse_to_StationResponse(raw_daily, station: FBACalculatorWeatherStation) -> StationResponse:
    """ Transform from the raw daily json object returned by wf1, to our fba_calc.StationResponse object.
    """
    bui = raw_daily.get('buildUpIndex', None)
    ffmc = raw_daily.get('fineFuelMoistureCode', None)
    isi = raw_daily.get('initialSpreadIndex', None)
    # time of interest will be the same for all stations
    time_of_interest = get_hour_20_from_date(station.time_of_interest)

    fmc = foliar_moisture_content(station.lat, station.long, station.elevation,
                                  get_julian_date(time_of_interest))
    sfc = surface_fuel_consumption(station.fuel_type, bui, ffmc, station.percentage_conifer)
    lb_ratio = length_to_breadth_ratio(station.fuel_type, raw_daily.get('windSpeed', None))
    ros = rate_of_spread(station.fuel_type, isi, bui, fmc, sfc,
                         pc=station.percentage_conifer,
                         cc=station.grass_cure,
                         pdf=station.percentage_dead_balsam_fir,
                         cbh=station.crown_base_height
                         )
    cfb = crown_fraction_burned(station.fuel_type, fmc, sfc, ros)
    hfi = head_fire_intensity(station, bui, ffmc, isi, ros)
    return StationResponse(
        station_code=station.code,
        date=station.time_of_interest,
        elevation=station.elevation,
        fuel_type=station.fuel_type,
        status="Observed" if raw_daily.get('recordType', '').get('id') == 'ACTUAL' else "Forecasted",
        temp=raw_daily.get('temperature', None),
        rh=raw_daily.get('relativeHumidity', None),
        wind_speed=raw_daily.get('windSpeed', None),
        wind_direction=raw_daily.get('windDirection', None),
        precipitation=raw_daily.get('precipitation', None),
        grass_cure=raw_daily.get('grasslandCuring', None),
        fine_fuel_moisture_code=ffmc,
        drought_code=raw_daily.get('droughtCode', None),
        initial_spread_index=isi,
        build_up_index=bui,
        duff_moisture_code=raw_daily.get('duffMoistureCode', None),
        fire_weather_index=raw_daily.get('fireWeatherIndex', None),
        head_fire_intensity=hfi,
        rate_of_spread=ros,
        fire_type=get_fire_type(cfb),
        percentage_crown_fraction_burned=cfb,
        flame_length=get_approx_flame_length(hfi),
        sixty_minute_fire_size=get_60_minutes_fire_size(lb_ratio, ros),
        thirty_minute_fire_size=get_30_minutes_fire_size(lb_ratio, ros),
    )


def replace_nones_in_hourly_actual_with_nan(hourly_reading: WeatherReading):
    """ Returns WeatherReading where any and all None values are replaced with math.nan
    in preparation for entry into database. Have to do this because Postgres doesn't
    handle None gracefully (it thinks None != None), but it can handle math.nan ok.
    (See HourlyActual db model) """
    if hourly_reading.temperature is None:
        hourly_reading.temperature = math.nan
    if hourly_reading.relative_humidity is None:
        hourly_reading.relative_humidity = math.nan
    if hourly_reading.precipitation is None:
        hourly_reading.precipitation = math.nan
    if hourly_reading.wind_direction is None:
        hourly_reading.wind_direction = math.nan
    if hourly_reading.wind_speed is None:
        hourly_reading.wind_speed = math.nan
    return hourly_reading


def parse_hourly_actual(station_code: int, hourly_reading: WeatherReading):
    """ Maps WeatherReading to HourlyActual """
    temp_valid = hourly_reading.temperature is not None
    rh_valid = hourly_reading.relative_humidity is not None and validate_metric(
        hourly_reading.relative_humidity, 0, 100)
    wdir_valid = hourly_reading.wind_direction is not None and validate_metric(
        hourly_reading.wind_direction, 0, 360)
    wspeed_valid = hourly_reading.wind_speed is not None and validate_metric(
        hourly_reading.wind_speed, 0, math.inf)
    precip_valid = hourly_reading.precipitation is not None and validate_metric(
        hourly_reading.precipitation, 0, math.inf)
    hourly_reading = replace_nones_in_hourly_actual_with_nan(hourly_reading)

    is_valid_wfwx = hourly_reading.observation_valid
    if is_valid_wfwx is False:
        logger.warning("Invalid hourly received from WF1 API for station code %s at time %s: %s",
                       station_code,
                       hourly_reading.datetime.strftime("%b %d %Y %H:%M:%S"),
                       hourly_reading.observation_valid_comment)

    is_obs_invalid = not temp_valid and not rh_valid and not wdir_valid\
        and not wspeed_valid and not precip_valid

    if is_obs_invalid:
        logger.error("Hourly actual not written to DB for station code %s at time %s: %s",
                     station_code, hourly_reading.datetime.strftime("%b %d %Y %H:%M:%S"),
                     hourly_reading.observation_valid_comment)

    # don't write the HourlyActual to our database if every value is invalid. If even one
    # weather variable observed is valid, write the HourlyActual to DB.
    return None if is_obs_invalid else HourlyActual(
        station_code=station_code,
        weather_date=hourly_reading.datetime,
        temp_valid=temp_valid,
        temperature=hourly_reading.temperature,
        rh_valid=rh_valid,
        relative_humidity=hourly_reading.relative_humidity,
        wspeed_valid=wspeed_valid,
        wind_speed=hourly_reading.wind_speed,
        wdir_valid=wdir_valid,
        wind_direction=hourly_reading.wind_direction,
        precip_valid=precip_valid,
        precipitation=hourly_reading.precipitation,
        dewpoint=hourly_reading.dewpoint,
        ffmc=hourly_reading.ffmc,
        isi=hourly_reading.isi,
        fwi=hourly_reading.fwi,
    )


def validate_metric(value, low, high):
    """ Validate metric with it's range of accepted values """
    return low <= value <= high
