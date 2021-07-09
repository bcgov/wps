""" Parsers that extract fields from WFWX API responses and build ours"""

import math
import logging
from datetime import datetime, timezone
from typing import Generator, List
from app.db.models.observations import HourlyActual
from app.schemas.fba_calc import StationResponse
from app.schemas.stations import WeatherStation
from app.utils import cffdrs
from app.utils.dewpoint import compute_dewpoint
from app.data.ecodivision_seasons import EcodivisionSeasons
from app.schemas.observations import WeatherReading
from app.schemas.hfi_calc import StationDaily
from app.utils.fba_calculator import (
    FBACalculatorWeatherStation,
    get_30_minutes_fire_size,
    get_60_minutes_fire_size,
    get_approx_flame_length,
    get_fire_type)
from app.utils.time import get_julian_date, get_julian_date_now, get_hour_20_from_date
from app.wildfire_one.util import is_station_valid

logger = logging.getLogger(__name__)

# PC, PDF, CC, CDH from the Red Book. Assumes values of 1 CBH.
# CC: Assume values of None for non grass types, and 0 for O1A and O1B.
# TODO: Store then in the DB as columns in FuelType
# CFL is based on Table 8, page 35, of "Development and Structure of the Canadian Forest Fire Behaviour
# Prediction System" from Forestry Canada Fire Danger Group, Information Report ST-X-3, 1992.
# For D1, D2, O1A, O1B, S1, S2 and S3 - a value of 1.0 is used.
# TODO: Establish correct method of calculating HFI for D1, D2, O1A, O1B, S1, S2 and S3
FUEL_TYPE_LOOKUP = {"C1": {"PC": 100, "PDF": 0, "CC": None, "CBH": 2, "CFL": 0.75},
                    "C2": {"PC": 100, "PDF": 0, "CC": None, "CBH": 3, "CFL": 0.8},
                    "C3": {"PC": 100, "PDF": 0, "CC": None, "CBH": 8, "CFL": 1.15},
                    "C4": {"PC": 100, "PDF": 0, "CC": None, "CBH": 4, "CFL": 1.2},
                    "C5": {"PC": 100, "PDF": 0, "CC": None, "CBH": 18, "CFL": 1.2},
                    # There's a 2m and 7m C6 in RB. Opted for 7m.
                    "C6": {"PC": 100, "PDF": 0, "CC": None, "CBH": 7, "CFL": 1.8},
                    "C7": {"PC": 100, "PDF": 0, "CC": None, "CBH": 10, "CFL": 0.5},
                    # No CBH listed in RB fire intensity class table for D1.
                    # Using default CBH value of 3, as specified in fbp.Rd in cffdrs R package.
                    "D1": {"PC": 0, "PDF": 0, "CC": None, "CBH": 3, "CFL": 1.0},  # TODO: check cfl
                    # No CBH listed in RB fire intensity class table for D2.
                    # Using default CBH value of 3, as specified in fbp.Rd in cffdrs R package.
                    "D2": {"PC": 0, "PDF": 0, "CC": None, "CBH": 3, "CFL": 1.0},  # TODO: check cfl
                    # 3 different PC configurations for M1. Opted for 50%.
                    "M1": {"PC": 50, "PDF": 0, "CC": None, "CBH": 6, "CFL": 0.8},
                    # 3 different PC configurations for M2. Opted for 50%.
                    "M2": {"PC": 50, "PDF": 0, "CC": None, "CBH": 6, "CFL": 0.8},
                    # 3 different PDF configurations for M3. Opted for 60%.
                    "M3": {"PC": 0, "PDF": 60, "CC": None, "CBH": 6, "CFL": 0.8},
                    # 3 different PDF configurations for M4. Opted for 60%.
                    "M4": {"PC": 0, "PDF": 60, "CC": None, "CBH": 6, "CFL": 0.8},
                    # NOTE! I think having a default CC of 0 is dangerous, I think we should rather just
                    # fail to calculate ROS, and say, unknown.
                    "O1A": {"PC": 0, "PDF": 0, "CC": 0, "CBH": 1, "CFL": 1.0},  # TODO: check cfl
                    "O1B": {"PC": 0, "PDF": 0, "CC": 0, "CBH": 1, "CFL": 1.0},  # TODO: check cfl
                    "S1": {"PC": 0, "PDF": 0, "CC": None, "CBH": 1, "CFL": 1.0},  # TODO: check cfl
                    "S2": {"PC": 0, "PDF": 0, "CC": None, "CBH": 1, "CFL": 1.0},  # TODO: check cfl
                    "S3": {"PC": 0, "PDF": 0, "CC": None, "CBH": 1, "CFL": 1.0}  # TODO: check cfl
                    }


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

    def __init__(self,  # pylint: disable=too-many-arguments
                 wfwx_id: str, code: int, latitude: float, longitude: float, elevation: int, name: str):
        self.wfwx_id = wfwx_id
        self.code = code
        self.name = name
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
                                               elevation=raw_station['elevation'],
                                               name=raw_station['displayLabel']
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


def generate_station_daily(raw_daily, station: WFWXWeatherStation, fuel_type: str) -> StationDaily:
    """ Transform from the raw daily json object returned by wf1, to our daily object.
    """
    # pylint: disable=invalid-name
    # we use the fuel type lookup to get default values.
    pc = FUEL_TYPE_LOOKUP[fuel_type]["PC"]
    pdf = FUEL_TYPE_LOOKUP[fuel_type]["PDF"]
    cbh = FUEL_TYPE_LOOKUP[fuel_type]["CBH"]

    isi = raw_daily.get('initialSpreadIndex', None)
    bui = raw_daily.get('buildUpIndex', None)
    ffmc = raw_daily.get('fineFuelMoistureCode', None)
    fmc = cffdrs.foliar_moisture_content(station.lat, station.long, station.elevation, get_julian_date_now())
    sfc = cffdrs.surface_fuel_consumption(fuel_type, bui, ffmc, pc)

    cc = raw_daily.get('grasslandCuring')
    if cc is None:
        cc = FUEL_TYPE_LOOKUP[fuel_type]["CC"]
    ros = cffdrs.rate_of_spread(fuel_type, isi, bui, fmc, sfc, pc=pc,
                                cc=cc,
                                pdf=pdf,
                                cbh=cbh)
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


def generate_station_response(raw_daily, station: FBACalculatorWeatherStation) -> StationResponse:
    """ Transform from the raw daily json object returned by wf1, to our fba_calc.StationResponse object.
    """
    bui = raw_daily.get('buildUpIndex', None)
    ffmc = raw_daily.get('fineFuelMoistureCode', None)
    isi = raw_daily.get('initialSpreadIndex', None)
    # time of interest will be the same for all stations
    time_of_interest = get_hour_20_from_date(station.time_of_interest)

    fmc = cffdrs.foliar_moisture_content(station.lat, station.long, station.elevation,
                                         get_julian_date(time_of_interest))
    sfc = cffdrs.surface_fuel_consumption(station.fuel_type, bui, ffmc, station.percentage_conifer)
    lb_ratio = cffdrs.length_to_breadth_ratio(station.fuel_type, raw_daily.get('windSpeed', None))
    ros = cffdrs.rate_of_spread(station.fuel_type, isi=isi, bui=bui, fmc=fmc, sfc=sfc,
                                pc=station.percentage_conifer,
                                cc=station.grass_cure,
                                pdf=station.percentage_dead_balsam_fir,
                                cbh=station.crown_base_height
                                )
    if station.fuel_type in ('D1', 'O1A', 'O1B', 'S1', 'S2', 'S3'):
        # These fuel types don't have a crown fraction burnt. But CFB is needed for other calculations,
        # so we go with 0.
        cfb = 0
    elif station.crown_base_height is None:
        # We can't calculate cfb without a crown base height!
        cfb = None
    else:
        cfb = cffdrs.crown_fraction_burned(station.fuel_type, fmc=fmc, sfc=sfc,
                                           ros=ros, cbh=station.crown_base_height)

    cfl = FUEL_TYPE_LOOKUP[station.fuel_type].get('CFL', None)

    hfi = cffdrs.head_fire_intensity(station, bui=bui, ffmc=ffmc, ros=ros, cfb=cfb, cfl=cfl)
    ffmc_for_hfi_4000, hfi_when_ffmc_equals_ffmc_for_hfi_4000 = cffdrs.get_ffmc_for_target_hfi(
        station, bui, ffmc, ros, cfb, cfl, 4000)
    ffmc_for_hfi_10000, hfi_when_ffmc_equals_ffmc_for_hfi_10000 = cffdrs.get_ffmc_for_target_hfi(
        station, bui, ffmc, ros, cfb, cfl, 10000)
    temp = raw_daily.get('temperature', None)
    rh = raw_daily.get('relativeHumidity', None)
    wind_speed = raw_daily.get('windSpeed', None)
    precip = raw_daily.get('precipitation', None)
    return StationResponse(
        station_code=station.code,
        station_name=station.name,
        date=station.time_of_interest,
        elevation=station.elevation,
        fuel_type=station.fuel_type,
        status="Observed" if raw_daily.get('recordType', '').get('id') == 'ACTUAL' else "Forecasted",
        temp=temp,
        rh=rh,
        wind_speed=wind_speed,
        wind_direction=raw_daily.get('windDirection', None),
        precipitation=precip,
        grass_cure=station.grass_cure,  # we ignore the grass cure from WF1 api, and return input back out
        fine_fuel_moisture_code=ffmc,
        drought_code=raw_daily.get('droughtCode', None),
        initial_spread_index=isi,
        build_up_index=bui,
        duff_moisture_code=raw_daily.get('duffMoistureCode', None),
        fire_weather_index=raw_daily.get('fireWeatherIndex', None),
        head_fire_intensity=hfi,
        rate_of_spread=ros,
        fire_type=get_fire_type(fuel_type=station.fuel_type, crown_fraction_burned=cfb),
        percentage_crown_fraction_burned=cfb,
        flame_length=get_approx_flame_length(hfi),
        sixty_minute_fire_size=get_60_minutes_fire_size(lb_ratio, ros),
        thirty_minute_fire_size=get_30_minutes_fire_size(lb_ratio, ros),
        ffmc_for_hfi_4000=ffmc_for_hfi_4000,
        hfi_when_ffmc_equals_ffmc_for_hfi_4000=hfi_when_ffmc_equals_ffmc_for_hfi_4000,
        ffmc_for_hfi_10000=ffmc_for_hfi_10000,
        hfi_when_ffmc_equals_ffmc_for_hfi_10000=hfi_when_ffmc_equals_ffmc_for_hfi_10000,
        critical_hours_hfi_4000=cffdrs.get_critical_hours(
            4000, station, bui, ffmc, ros, cfb, cfl, temp, rh, wind_speed, precip),
        critical_hours_hfi_10000=cffdrs.get_critical_hours(
            10000, station, bui, ffmc, ros, cfb, cfl, temp, rh, wind_speed, precip)
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
