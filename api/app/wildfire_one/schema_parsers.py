""" Parsers that extract fields from WFWX API responses and build ours"""

import math
import logging
from datetime import datetime, timezone
from typing import Generator, List, Optional
from app.db.models.observations import HourlyActual
from app.schemas.fba_calc import FuelTypeEnum
from app.schemas.stations import WeatherStation
from app.utils import cffdrs
from app.utils import c7b
from app.utils.dewpoint import compute_dewpoint
from app.data.ecodivision_seasons import EcodivisionSeasons
from app.schemas.observations import WeatherReading
from app.db.models.forecasts import NoonForecast
from app.schemas.hfi_calc import StationDaily
from app.utils.fuel_types import FUEL_TYPE_DEFAULTS
from app.fba_calculator import calculate_cfb, get_fire_size, get_fire_type
from app.utils.time import get_julian_date_now, get_utc_now
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


def calculate_intensity_group(hfi: float) -> int:
    """ Returns a 1-5 integer value indicating Intensity Group based on HFI.
    Intensity groupings are:

    HFI             IG
    0-499            1
    500-999          2
    1000-1999        3
    2000-3999        4
    4000+            5
    """
    if hfi < 500:
        return 1
    if hfi < 1000:
        return 2
    if hfi < 2000:
        return 3
    if hfi < 4000:
        return 4
    return 5


class FireBehaviourPrediction:
    """ Structure for storing fire behaviour prediction data. """

    def __init__(self, ros: float,
                 hfi: float, intensity_group,
                 sixty_minute_fire_size: float,
                 fire_type) -> None:
        self.ros = ros
        self.hfi = hfi
        self.intensity_group = intensity_group
        self.sixty_minute_fire_size = sixty_minute_fire_size
        self.fire_type = fire_type


def calculate_fire_behaviour_prediction_using_cffdrs(  # pylint: disable=too-many-arguments
        latitude: float,
        longitude: float,
        elevation: float,
        fuel_type: FuelTypeEnum,
        bui: float,
        ffmc: float,
        cc: float,  # pylint: disable=invalid-name
        pc: float,  # pylint: disable=invalid-name
        wind_speed: float,
        isi: float,
        pdf: float,
        cbh: float,
        cfl: float):
    """ Calculates fire behaviour prediction using CFFDRS. """
    # pylint: disable=too-many-locals

    # set default values in case the calculation fails (likely due to missing data)
    fmc = cffdrs.foliar_moisture_content(latitude, longitude, elevation, get_julian_date_now())
    sfc = cffdrs.surface_fuel_consumption(fuel_type, bui, ffmc, pc)
    if cc is None:
        cc = FUEL_TYPE_DEFAULTS[fuel_type]["CC"]

    ros = cffdrs.rate_of_spread(FuelTypeEnum[fuel_type], isi, bui, fmc, sfc, pc=pc,
                                cc=cc,
                                pdf=pdf,
                                cbh=cbh)
    if sfc is not None:
        cfb = calculate_cfb(FuelTypeEnum[fuel_type], fmc, sfc, ros, cbh)

    if ros is not None and cfb is not None and cfl is not None:
        hfi = cffdrs.head_fire_intensity(fuel_type=FuelTypeEnum[fuel_type],
                                         percentage_conifer=pc,
                                         percentage_dead_balsam_fir=pdf,
                                         ros=ros, cfb=cfb, cfl=cfl, sfc=sfc)

    lb_ratio = cffdrs.length_to_breadth_ratio(FuelTypeEnum[fuel_type], wind_speed)
    wsv = cffdrs.calculate_wind_speed(FuelTypeEnum[fuel_type],
                                      ffmc=ffmc,
                                      bui=bui,
                                      ws=wind_speed,
                                      fmc=fmc,
                                      sfc=sfc,
                                      pc=pc,
                                      cc=cc,
                                      pdf=pdf,
                                      cbh=cbh,
                                      isi=isi)

    bros = cffdrs.back_rate_of_spread(FuelTypeEnum[fuel_type],
                                      ffmc=ffmc,
                                      bui=bui,
                                      wsv=wsv,
                                      fmc=fmc, sfc=sfc,
                                      pc=pc,
                                      cc=cc,
                                      pdf=pdf,
                                      cbh=cbh)

    sixty_minute_fire_size = get_fire_size(FuelTypeEnum[fuel_type], ros, bros, 60, cfb, lb_ratio)

    fire_type = get_fire_type(FuelTypeEnum[fuel_type], crown_fraction_burned=cfb)

    if hfi is not None:
        intensity_group = calculate_intensity_group(hfi)

    fire_behaviour_prediction = FireBehaviourPrediction(ros=ros, hfi=hfi, intensity_group=intensity_group,
                                                        sixty_minute_fire_size=sixty_minute_fire_size,
                                                        fire_type=fire_type)
    return fire_behaviour_prediction


def calculate_fire_behaviour_prediction_using_c7b(latitude: float,
                                                  longitude: float,
                                                  elevation: float,
                                                  ffmc: float,
                                                  bui: float,
                                                  wind_speed: float,
                                                  cc: float,  # pylint: disable=invalid-name
                                                  cbh: float,
                                                  cfl: float):
    """ Calculates fire behaviour prediction using C7B. """

    ros = c7b.rate_of_spread(ffmc=ffmc, bui=bui, wind_speed=wind_speed, percentage_slope=0.0, cc=cc)

    fmc = cffdrs.foliar_moisture_content(latitude, longitude, elevation, get_julian_date_now())

    sfc = cffdrs.surface_fuel_consumption(fuel_type=FuelTypeEnum.C7, bui=bui, ffmc=ffmc, pc=None)
    cfb = cffdrs.crown_fraction_burned(fuel_type=FuelTypeEnum.C7, fmc=fmc,
                                       sfc=sfc, ros=ros, cbh=cbh)

    hfi = cffdrs.head_fire_intensity(fuel_type=FuelTypeEnum.C7,
                                     percentage_conifer=None,
                                     percentage_dead_balsam_fir=None,
                                     ros=ros, cfb=cfb, cfl=cfl, sfc=sfc)

    fire_type = get_fire_type(FuelTypeEnum.C7B, cfb)

    intensity_group = calculate_intensity_group(hfi)

    # TODO: not required for HFI, but for FireBat - we need to calculate 60 minute fire size, which
    # will take a fair amount of peeking at the math.
    # Some of the math in the c7b.rate_of_spread can be extracted, and the standard cffdrs math used.
    fire_behaviour_prediction = FireBehaviourPrediction(
        ros=ros,
        hfi=hfi,
        intensity_group=intensity_group,
        sixty_minute_fire_size=None,
        fire_type=fire_type)

    return fire_behaviour_prediction


def calculate_fire_behaviour_prediction(latitude: float,  # pylint: disable=too-many-arguments
                                        longitude: float, elevation: float,
                                        fuel_type: FuelTypeEnum,
                                        bui: float, ffmc: float, wind_speed: float,
                                        cc: float,  # pylint: disable=invalid-name
                                        pc: float,  # pylint: disable=invalid-name
                                        isi: float, pdf: float, cbh: float, cfl: float):
    """ Calculate the fire behaviour prediction. """
    if fuel_type == FuelTypeEnum.C7B:
        return calculate_fire_behaviour_prediction_using_c7b(
            latitude=latitude,
            longitude=longitude,
            elevation=elevation,
            ffmc=ffmc,
            bui=bui,
            wind_speed=wind_speed,
            cc=cc,
            cbh=cbh,
            cfl=cfl)
    return calculate_fire_behaviour_prediction_using_cffdrs(
        latitude=latitude,
        longitude=longitude,
        elevation=elevation,
        fuel_type=fuel_type,
        bui=bui,
        ffmc=ffmc,
        cc=cc,
        pc=pc,
        wind_speed=wind_speed,
        isi=isi,
        pdf=pdf,
        cbh=cbh,
        cfl=cfl)


def generate_station_daily(raw_daily,  # pylint: disable=too-many-locals
                           station: WFWXWeatherStation,
                           fuel_type: str) -> StationDaily:
    """ Transform from the raw daily json object returned by wf1, to our daily object.
    """
    # pylint: disable=invalid-name
    # we use the fuel type lookup to get default values.
    pc = FUEL_TYPE_DEFAULTS[fuel_type]["PC"]
    pdf = FUEL_TYPE_DEFAULTS[fuel_type]["PDF"]
    cbh = FUEL_TYPE_DEFAULTS[fuel_type]["CBH"]
    cfl = FUEL_TYPE_DEFAULTS[fuel_type]["CFL"]
    date = raw_daily.get('weatherTimestamp', None)
    isi = raw_daily.get('initialSpreadIndex', None)
    bui = raw_daily.get('buildUpIndex', None)
    ffmc = raw_daily.get('fineFuelMoistureCode', None)
    cc = raw_daily.get('grasslandCuring', None)
    wind_speed = raw_daily.get('windSpeed', None)

    try:
        fire_behaviour_prediction = calculate_fire_behaviour_prediction(
            latitude=station.lat,
            longitude=station.long,
            elevation=station.elevation,
            fuel_type=FuelTypeEnum[fuel_type],
            bui=bui,
            ffmc=ffmc,
            wind_speed=wind_speed,
            cc=cc,
            pc=pc,
            isi=isi,
            pdf=pdf,
            cbh=cbh,
            cfl=cfl)
    # pylint: disable=broad-except
    except Exception as exc:
        logger.error('Encountered error while generating StationDaily for station %s', station.code)
        logger.error(exc, exc_info=True)
        # prediction calculation failed, so we set the values to None
        fire_behaviour_prediction = FireBehaviourPrediction(None, None, None, None, None)

    return StationDaily(
        code=station.code,
        date=date,
        status=raw_daily.get('recordType', '').get('id', None),
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
        rate_of_spread=fire_behaviour_prediction.ros,
        hfi=fire_behaviour_prediction.hfi,
        observation_valid=raw_daily.get('observationValidInd', None),
        observation_valid_comment=raw_daily.get(
            'observationValidComment', None),
        intensity_group=fire_behaviour_prediction.intensity_group,
        sixty_minute_fire_size=fire_behaviour_prediction.sixty_minute_fire_size,
        fire_type=fire_behaviour_prediction.fire_type,
        error=raw_daily.get('observationValidInd', None),
        error_message=raw_daily.get('observationValidComment', None),
        last_updated=datetime.fromtimestamp(raw_daily.get(
            'lastEntityUpdateTimestamp') / 1000, tz=timezone.utc)
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
