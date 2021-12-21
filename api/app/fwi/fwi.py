
from typing import Optional
from app.utils import cffdrs


def fwi_bui(dmc: Optional[float], dc: Optional[float]):
    if dmc is None or dc is None:
        return None

    return cffdrs.bui_calc(dmc, dc)


def fwi_isi(ffmc: Optional[float], wind_speed: Optional[float]):
    if ffmc is None or wind_speed is None:
        return None
    return cffdrs.initial_spread_index(ffmc, wind_speed)


def fwi_ffmc(
        ffmc: Optional[float],
        temperature: Optional[float],
        relative_humidity: Optional[float],
        precipitation: Optional[float],
        wind_speed: Optional[float]
):
    if ffmc is None or temperature is None or relative_humidity is None or precipitation is None or wind_speed is None:
        return None
    return cffdrs.fine_fuel_moisture_code(ffmc, temperature, relative_humidity, precipitation, wind_speed)


def fwi_fwi(isi: Optional[float], bui: Optional[float]):
    if isi is None or bui is None:
        return None
    return cffdrs.fire_weather_index(isi, bui)
