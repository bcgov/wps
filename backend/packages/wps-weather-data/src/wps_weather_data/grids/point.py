"""One location's forecast from a model's grids, in the same units for every model.

The stores hold what each provider published, so the units and some of the variables differ by
model. These are the units the station model values are in.
"""

from datetime import datetime, timedelta

import numpy as np
import pyarrow as pa

from wps_weather_data.grids.store import GridStore

KELVIN = 273.15
KM_H_PER_M_S = 3.6
# What precipitation is multiplied by to be in mm, by the units it is published in.
TO_MM = {"mm since the run started": 1, "m since the run started": 1000}


def relative_humidity(temperature: np.ndarray, dewpoint: np.ndarray) -> np.ndarray:
    """Relative humidity, by the formula the ECMWF station job uses.

    :param temperature: Air temperature, °C
    :param dewpoint: Dew point, °C
    :return: Relative humidity, %
    """

    def vapour_pressure(celsius: np.ndarray) -> np.ndarray:
        return np.exp(17.625 * celsius / (celsius + 243.04))

    return 100 * vapour_pressure(dewpoint) / vapour_pressure(temperature)


def wind_from_components(u: np.ndarray, v: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Wind speed and direction from its components.

    :param u: The component towards the east
    :param v: The component towards the north
    :return: The speed, in the components' units, and the direction the wind blows from, in
        degrees clockwise from north
    """
    return np.hypot(u, v), np.degrees(np.arctan2(-u, -v)) % 360


def read_point_forecast(store: GridStore, run_time: datetime, y: int, x: int) -> pa.Table:
    """A grid cell's forecast for a run, in the same units for every model.

    :param store: The store to read the run from
    :param run_time: UTC start of the run
    :param y: The cell's row, as `GridStore.nearest_cell` gives it
    :param x: The cell's column
    :return: A row per forecast hour: temperature in °C, relative humidity in %, wind speed in
        km/h and direction in degrees, and precipitation since the row before in mm
    :raises KeyError: If the store does not have the run
    """
    point = store.read_point(run_time, y, x)
    hours = point["forecast_hour"]
    temperature = point["temperature"] - KELVIN
    if "relative_humidity" in point:
        humidity = point["relative_humidity"]
    else:
        humidity = relative_humidity(temperature, point["dewpoint"] - KELVIN)
    if "wind_speed" in point:
        speed, direction = point["wind_speed"], point["wind_direction"]
    else:
        speed, direction = wind_from_components(point["wind_u"], point["wind_v"])
    units = {variable.name: variable.units for variable in store.model.variables}
    total = point["precipitation"] * TO_MM[units["precipitation"]]
    # A total can fall by a step of its packing from one hour to the next.
    precipitation = np.maximum(np.diff(total, prepend=0.0), 0.0)
    utc = pa.timestamp("us", tz="UTC")
    return pa.table(
        {
            "timestamp": pa.array([run_time + timedelta(hours=int(hour)) for hour in hours], utc),
            "run_timestamp": pa.array([run_time] * len(hours), utc),
            "forecast_hour": pa.array(hours, pa.int32()),
            "temperature": pa.array(temperature, pa.float32()),
            "relative_humidity": pa.array(humidity, pa.float32()),
            "wind_speed": pa.array(speed * KM_H_PER_M_S, pa.float32()),
            "wind_direction": pa.array(direction, pa.float32()),
            "precipitation": pa.array(precipitation, pa.float32()),
        }
    )
