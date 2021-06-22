""" Parsers that extract fields from WFWX API responses and build ours"""

from datetime import datetime, timezone
from app.schemas.stations import WeatherStation
from app.utils.dewpoint import compute_dewpoint
from app.data.ecodivision_seasons import EcodivisionSeasons
from app.schemas.observations import WeatherReading
from app.schemas.hfi_calc import StationDaily


def _parse_station(station) -> WeatherStation:
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


def _parse_hourly(hourly) -> WeatherReading:
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


def _parse_daily(raw_daily, station_code) -> StationDaily:
    """ Transform from the raw hourly json object returned by wf1, to our hourly object.
    """
    return StationDaily(
        code=station_code,
        status="Observed" if raw_daily.get('recordType', '').get('id') == 'ACTUAL' else "Forecasted",
        temperature=raw_daily.get('temperature', None),
        relative_humidity=raw_daily.get('relativeHumidity', None),
        wind_speed=raw_daily.get('windSpeed', None),
        wind_direction=raw_daily.get('windDirection', None),
        precipitation=raw_daily.get('precipitation', None),
        grass_cure_percentage=raw_daily.get('grasslandCuring', None),
        ffmc=raw_daily.get('fineFuelMoistureCode', None),
        dmc=raw_daily.get('duffMoistureCode', None),
        dc=raw_daily.get('droughtCode', None),
        isi=raw_daily.get('initialSpreadIndex', None),
        bui=raw_daily.get('buildUpIndex', None),
        fwi=raw_daily.get('fireWeatherIndex', None),
        danger_class=raw_daily.get('dailySeverityRating', None),
        observation_valid=raw_daily.get('observationValidInd', None),
        observation_valid_comment=raw_daily.get('observationValidComment', None)
    )
