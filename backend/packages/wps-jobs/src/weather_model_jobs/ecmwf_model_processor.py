from collections.abc import Sequence

import numpy as np
import wps_nwp as nwp
from wps_shared.db.models.weather_models import ModelRunPrediction

from weather_model_jobs.utils.process_grib import (
    calculate_relative_humidity,
    convert_kelvin_to_celsius,
    convert_mps_to_kph,
)

# What is fetched for each forecast hour. ECMWF does not publish relative humidity or wind
# speed and direction, so those are derived from the dewpoint and the wind components.
VARIABLES = (
    nwp.Variable.T2M,
    nwp.Variable.D2M,
    nwp.Variable.U10,
    nwp.Variable.V10,
    nwp.Variable.PRECIP,
)


async def station_values(fields: Sequence[nwp.Field], lats, lons) -> dict[str, np.ndarray]:
    """
    Turn one forecast hour's fields into the values stored for each station.

    :param fields: one field for each of VARIABLES, all for the same forecast hour
    :param lats: latitude of each station
    :param lons: longitude of each station
    :return: ModelRunPrediction field name -> one value per station, in the order of lats
    """
    sampled = await nwp.sample(fields, lats, lons)
    values = {field.variable: array for field, array in zip(fields, sampled)}
    temperature = values[nwp.Variable.T2M]
    u, v = values[nwp.Variable.U10], values[nwp.Variable.V10]

    return {
        ModelRunPrediction.tmp_tgl_2.name: convert_kelvin_to_celsius(temperature),
        ModelRunPrediction.rh_tgl_2.name: calculate_relative_humidity(
            temperature, values[nwp.Variable.D2M]
        ),
        ModelRunPrediction.apcp_sfc_0.name: values[nwp.Variable.PRECIP],  # already in mm
        ModelRunPrediction.wind_tgl_10.name: convert_mps_to_kph(np.hypot(u, v)),
        # the direction the wind blows from, in degrees clockwise from north
        ModelRunPrediction.wdir_tgl_10.name: (270 - np.degrees(np.arctan2(v, u))) % 360,
    }
