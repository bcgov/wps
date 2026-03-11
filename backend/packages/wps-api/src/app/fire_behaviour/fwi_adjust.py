from datetime import datetime

from app.fire_behaviour import cffdrs
from wps_shared.schemas.fba_calc import StationRequest, AdjustedFWIResult
from wps_shared.schemas.stations import WFWXWeatherStation

"""
If user has not specified wind speed and/or precipitation, use the values retrieved from WFWX, always re-calculate FFMC & ISI
"""


def calculate_adjusted_fwi_result(
    requested_station: StationRequest,
    wfwx_station: WFWXWeatherStation,
    time_of_interest: datetime,
    yesterday: dict,
    raw_daily: dict,
) -> AdjustedFWIResult:
    # extract variable from wf1 that we need to calculate the fire behaviour advisory.

    temperature = raw_daily.get("temperature", None)
    relative_humidity = raw_daily.get("relativeHumidity", None)
    precipitation = raw_daily.get("precipitation", None)
    dmc = raw_daily.get("duffMoistureCode", None)
    dc = raw_daily.get("droughtCode", None)
    bui = cffdrs.bui_calc(dmc, dc)
    wind_speed = raw_daily.get("windSpeed", None)
    status = raw_daily.get("recordType").get("id")

    if requested_station.precipitation is not None:
        precipitation = requested_station.precipitation
        dmc = cffdrs.duff_moisture_code(
            yesterday.get("duffMoistureCode", None),
            temperature,
            relative_humidity,
            precipitation,
            wfwx_station.lat,
            time_of_interest.month,
        )
        dc = cffdrs.drought_code(
            yesterday.get("droughtCode", None),
            temperature,
            relative_humidity,
            precipitation,
            wfwx_station.lat,
            time_of_interest.month,
        )
        bui = cffdrs.bui_calc(dmc, dc)
        status = "ADJUSTED"

    if requested_station.wind_speed is not None:
        wind_speed = requested_station.wind_speed
        status = "ADJUSTED"

    ffmc = cffdrs.fine_fuel_moisture_code(
        yesterday.get("fineFuelMoistureCode", None),
        temperature,
        relative_humidity,
        precipitation,
        wind_speed,
    )
    isi = cffdrs.initial_spread_index(ffmc, wind_speed)
    fwi = cffdrs.fire_weather_index(isi, bui)

    missing = [name for name, val in (("ffmc", ffmc), ("bui", bui), ("isi", isi), ("fwi", fwi)) if val is None]
    if missing:
        raise ValueError(f"Insufficient weather data for station — could not compute: {', '.join(missing)}")

    return AdjustedFWIResult(
        ffmc=ffmc,
        isi=isi,
        bui=bui,
        dmc=dmc,
        dc=dc,
        precipitation=precipitation,
        wind_speed=wind_speed,
        fwi=fwi,
        status=status,
    )
