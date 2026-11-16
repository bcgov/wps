"""MoreCast's model values, read from the `by_time` table.

The same read as `wps_shared.weather_models.fetch.predictions`, which uses Postgres: the
20:00 UTC prediction per station, day and model, raw and bias-adjusted. `by_time` already
keeps one daily row per station, time and model, from the newest run, so this is a single read
with no choosing between runs.

MoreCast does not read this yet. backend/scripts/morecast_by_time_parity_check.py compares the
two.
"""

from collections.abc import Sequence
from datetime import datetime

from wps_shared.schemas.morecast_v2 import WeatherIndeterminate
from wps_shared.schemas.stations import WeatherStation
from wps_shared.weather_models import ModelEnum

from wps_weather_data.by_time import DAILY, ByTimeTable

# MoreCast does not show ECMWF.
MORECAST_MODELS = tuple(model for model in ModelEnum if model != ModelEnum.ECMWF)


def fetch_model_predictions(
    by_time: ByTimeTable,
    all_stations: Sequence[WeatherStation],
    start_time: datetime,
    end_time: datetime,
) -> list[WeatherIndeterminate]:
    """Get the daily model predictions for the stations with a time in [start_time, end_time].

    Each row becomes two WeatherIndeterminates, one for the model's values and one for the
    bias-adjusted values.
    """
    stations = {station.code: station for station in all_stations}
    rows = by_time.read(
        DAILY,
        [model.value for model in MORECAST_MODELS],
        start_time,
        end_time,
        station_codes=list(stations),
    )
    results = []
    for row in rows.to_pylist():
        shared = {
            "station_code": row["station_code"],
            "station_name": stations[row["station_code"]].name,
            "utc_timestamp": row["timestamp"],
            "prediction_run_timestamp": row["run_ts"],
        }
        results.append(
            WeatherIndeterminate(
                determinate=row["source"],
                temperature=row["temperature"],
                relative_humidity=row["relative_humidity"],
                precipitation=row["precipitation"],
                wind_direction=row["wind_direction"],
                wind_speed=row["wind_speed"],
                **shared,
            )
        )
        results.append(
            WeatherIndeterminate(
                determinate=f"{row['source']}_BIAS",
                temperature=row["bias_adjusted_temperature"],
                relative_humidity=row["bias_adjusted_relative_humidity"],
                precipitation=row["bias_adjusted_precipitation"],
                wind_direction=row["bias_adjusted_wind_direction"],
                wind_speed=row["bias_adjusted_wind_speed"],
                **shared,
            )
        )
    return results
