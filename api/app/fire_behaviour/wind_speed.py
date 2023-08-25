

from app.fire_behaviour import cffdrs
from app.schemas.fba_calc import StationRequest, WindResult

"""
If user has not specified wind speed, use the values retrieved from WFWX, always re-calculate FFMC & ISI
"""


def calculate_wind_speed_result(requested_station: StationRequest, yesterday: dict, raw_daily: dict) -> WindResult:
    # extract variable from wf1 that we need to calculate the fire behaviour advisory.
    bui = raw_daily.get('buildUpIndex', None)
    temperature = raw_daily.get('temperature', None)
    relative_humidity = raw_daily.get('relativeHumidity', None)
    precipitation = raw_daily.get('precipitation', None)

    wind_speed = raw_daily.get('windSpeed', None)
    status = raw_daily.get('recordType').get('id')

    if requested_station.wind_speed is not None:
        wind_speed = requested_station.wind_speed
        status = 'ADJUSTED'

    ffmc = cffdrs.fine_fuel_moisture_code(
        yesterday.get('fineFuelMoistureCode', None),
        temperature,
        relative_humidity,
        precipitation,
        wind_speed)
    isi = cffdrs.initial_spread_index(ffmc, wind_speed)
    fwi = cffdrs.fire_weather_index(isi, bui)
    return WindResult(ffmc=ffmc, isi=isi, wind_speed=wind_speed, fwi=fwi, status=status)
