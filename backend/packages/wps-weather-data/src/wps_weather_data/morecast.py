"""MoreCast's model values, read from the `by_time` table.

The 20:00 UTC prediction per station, day and model, raw and bias-adjusted. `by_time` already
keeps one daily row per station, time and model, from the newest run, so this is a single read
with no choosing between runs. The MoreCast determinates route reads this.
"""

import logging
from collections.abc import Sequence
from datetime import datetime
from time import perf_counter

from wps_shared.schemas.morecast_v2 import WeatherIndeterminate
from wps_shared.schemas.stations import WeatherStation
from wps_shared.weather_models import ModelEnum

from wps_weather_data.by_time import DAILY, ByTimeTable

logger = logging.getLogger(__name__)

# Every model, ECMWF included. ECMWF's runs are from its 0.1° grid only: its job reads no other,
# and the backfill from Postgres took the 0.1° run where both grids had one.
MORECAST_MODELS = tuple(ModelEnum)


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
    started = perf_counter()
    stations = {station.code: station for station in all_stations}
    rows = by_time.read(
        DAILY,
        [model.value for model in MORECAST_MODELS],
        start_time,
        end_time,
        station_codes=list(stations),
    )
    read_seconds = perf_counter() - started
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
    logger.info(
        "Read %d by_time rows for %d stations from %s to %s in %.3f s (%.3f s in total)",
        rows.num_rows,
        len(stations),
        start_time,
        end_time,
        read_seconds,
        perf_counter() - started,
    )
    return results
