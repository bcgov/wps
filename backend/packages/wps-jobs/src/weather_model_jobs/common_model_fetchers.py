"""What the model jobs share: staging a run's files as they are processed, deciding whether a run
is already published, and turning a fully staged run into station predictions.

A run is downloaded into `staging`, then published: its station predictions are appended to
`runs`, merged into `by_time`, and the run is deleted from `staging`, in that order. A run in
`runs` with nothing left in `staging` is done. A run in both was interrupted while publishing, and
is published again.

Design: docs/architecture/station-weather-storage.md
"""

import logging
from collections.abc import Iterable
from datetime import datetime, timedelta, timezone
from typing import List

import numpy
import numpy as np
from pyproj import Geod
from weather_model_jobs.machine_learning import (
    StationMachineLearning,
    read_model_history,
    read_observations,
)
from weather_model_jobs.model_history import ModelHistory
from weather_model_jobs.model_values import ModelValues, StationPrediction
from weather_model_jobs.utils.interpolate import (
    construct_interpolated_noon_prediction,
    interpolate_bearing,
    interpolate_between_two_points,
)
from wps_shared.schemas.stations import WeatherStation
from wps_shared.weather_models import ModelEnum, adjust_model_day
from wps_shared.wps_logging import configure_logging
from wps_weather_data.actuals import StationObservations, get_accumulated_precipitation
from wps_weather_data.by_time import ByTimeTable
from wps_weather_data.runs import RunsTable
from wps_weather_data.staging import StagedFile, StagingTable
from wps_wf1.wfwx_api import get_stations_synchronously

# If running as its own process, configure logging appropriately.
if __name__ == "__main__":
    configure_logging()

logger = logging.getLogger(__name__)

# Keys for weather variables that require interpolation between 1800 and 2100
SCALAR_MODEL_VALUE_KEYS_FOR_INTERPOLATION = ("tmp_tgl_2", "rh_tgl_2", "wind_tgl_10", "apcp_sfc_0")

# How many processed files to stage per commit. A job that dies loses the files it has not staged
# yet, and fetches them again on its next run.
FILES_PER_STAGING_COMMIT = 50


def get_closest_index(coordinate: List, points: List):
    """Get the index of the point closest to the coordinate"""
    # https://pyproj4.github.io/pyproj/stable/api/geod.html
    # Use GRS80 ellipsoid (it's what NAD83 uses)
    geod = Geod(ellps="GRS80")
    # Calculate the distance each point is from the coordinate.
    _, _, distances = geod.inv(
        [coordinate[0] for _ in range(4)],
        [coordinate[1] for _ in range(4)],
        [x[0] for x in points],
        [x[1] for x in points],
    )
    # Return the index of the point with the shortest distance.
    return numpy.argmin(distances)


def model_run_timestamp(now: datetime, model_run_hour: int) -> datetime:
    """The start of the newest run at model_run_hour, as of now."""
    timestamp = datetime(now.year, now.month, now.day, now.hour, tzinfo=timezone.utc)
    return adjust_model_day(timestamp, model_run_hour).replace(hour=model_run_hour)


def run_is_published(
    runs_table: RunsTable, staging_table: StagingTable, model: ModelEnum, run_ts: datetime
) -> bool:
    """Whether a run is done: in `runs`, with nothing left in `staging`."""
    return runs_table.has_run(model, run_ts) and not staging_table.has_run(run_ts)


class RunStager:
    """Stages the files of one run as they are processed, in batches, and knows which of the run's
    files have been processed by this or an earlier invocation."""

    def __init__(self, staging_table: StagingTable, run_ts: datetime):
        self.staging_table = staging_table
        self.run_ts = run_ts
        self.processed = staging_table.processed_sources(run_ts)
        self._pending: list[StagedFile] = []

    def is_processed(self, source: str) -> bool:
        return source in self.processed or any(staged.source == source for staged in self._pending)

    def add(self, source: str, prediction_timestamp: datetime, values: list[tuple]):
        """Add a processed file and its station values. Staged with the next commit."""
        self._pending.append(StagedFile(source, prediction_timestamp, values))
        if len(self._pending) >= FILES_PER_STAGING_COMMIT:
            self.flush()

    def flush(self):
        """Stage the files added since the last commit."""
        if not self._pending:
            return
        self.staging_table.append_files(self.run_ts, self._pending)
        self.processed.update(staged.source for staged in self._pending)
        self._pending = []

    def is_complete(self, sources: Iterable[str]) -> bool:
        """Whether every one of the run's files has been staged."""
        sources = set(sources)
        logger.info("we have processed %s/%s files", len(sources & self.processed), len(sources))
        return bool(sources) and sources <= self.processed


def accumulate_nam_precipitation(
    nam_cumulative_precip: float, prediction: ModelValues, model_run_hour: int
):
    """Calculate overall cumulative precip and cumulative precip for the current prediction."""
    # 00 and 12 hour model runs accumulate precipitation in 12 hour intervals, 06 and 18 hour accumulate in
    # 3 hour intervals
    nam_accumulation_interval = 3 if model_run_hour == 6 or model_run_hour == 18 else 12
    cumulative_precip = nam_cumulative_precip
    prediction_precip = prediction.apcp_sfc_0 or 0.0
    current_precip = numpy.add(nam_cumulative_precip, prediction_precip)
    if prediction.prediction_timestamp.hour % nam_accumulation_interval == 0:
        # If we're on an 'accumulation interval', update the cumulative precip
        cumulative_precip = current_precip

    cumulative_precip = (
        cumulative_precip.item() if isinstance(cumulative_precip, np.float64) else cumulative_precip
    )
    current_precip = (
        current_precip.item() if isinstance(current_precip, np.float64) else current_precip
    )

    return (cumulative_precip, current_precip)


class ModelValueProcessor:
    """Turn fully staged model runs into station predictions, and publish them."""

    def __init__(
        self,
        model_type: ModelEnum,
        runs_table: RunsTable | None = None,
        by_time_table: ByTimeTable | None = None,
        staging_table: StagingTable | None = None,
    ):
        self.model_type = model_type
        self.stations = get_stations_synchronously()
        self.station_count = len(self.stations)
        self.runs_table = runs_table or RunsTable()
        self.by_time_table = by_time_table or ByTimeTable()
        self.staging_table = staging_table or StagingTable(model_type)
        # The observations for the run being published: read once per run, for training and for
        # the observed precip that a run's first day of 24 hour precip adds.
        self.observations = StationObservations({})

    def process(self, run_timestamps: Iterable[datetime]):
        """Publish each of the runs, which must be fully staged."""
        for run_ts in run_timestamps:
            start_time = datetime.now()
            self.publish_run(run_ts)
            execution_time = datetime.now() - start_time
            logger.info(
                "Interpolated & machine learned %s model run %s in %s",
                self.model_type.value,
                run_ts,
                execution_time,
            )

    def publish_run(self, run_ts: datetime):
        """Compute a staged run's station predictions, append them to `runs`, merge them into
        `by_time`, then delete the run from `staging`."""
        logger.info("Interpolating values for %s model run %s", self.model_type.value, run_ts)
        staged = self.staging_table.station_values(run_ts)
        history = read_model_history(self.runs_table, self.model_type, run_ts)
        self.observations = read_observations(self.by_time_table, run_ts)
        rows = []
        for index, station in enumerate(self.stations):
            values = staged.get(station.code)
            if not values:
                continue
            logger.info(
                "Interpolating model run %s (%s/%s) for %s:%s",
                run_ts,
                index,
                self.station_count,
                station.code,
                station.name,
            )
            predictions = [ModelValues.from_staging(station.code, value) for value in values]
            station_predictions = self._process_model_run_for_station(
                run_ts, station, predictions, history
            )
            rows.extend(prediction.as_row() for prediction in station_predictions)
        if not rows:
            # Kept in staging: deleting it would make the next run download it all again.
            logger.error(
                "No station predictions for %s model run %s, leaving it in staging",
                self.model_type.value,
                run_ts,
            )
            return
        self.runs_table.append_run(self.model_type, run_ts, rows)
        self.by_time_table.merge_run(self.model_type, run_ts, rows)
        self.staging_table.delete_run(run_ts)

    def _add_interpolated_bias_adjustments_to_prediction(
        self, station_prediction: StationPrediction, machine: StationMachineLearning
    ):
        # The model only has 3-hourly output, so there is no 2000 prediction to bias adjust directly.
        # Instead, bias adjust the 1800 and 2100 predictions and interpolate between them to get 2000.

        # Datetime constants for the interpolation points
        time_1800 = station_prediction.prediction_timestamp.replace(hour=18)
        time_2000 = station_prediction.prediction_timestamp.replace(hour=20)
        time_2100 = station_prediction.prediction_timestamp.replace(hour=21)

        # Predict the temperature
        temp_at_1800 = machine.predict_temperature(station_prediction.tmp_tgl_2, time_1800)
        temp_at_2100 = machine.predict_temperature(station_prediction.tmp_tgl_2, time_2100)
        station_prediction.bias_adjusted_temperature = interpolate_between_two_points(
            18, 21, temp_at_1800, temp_at_2100, 20
        )
        # Predict the rh
        rh_at_1800 = machine.predict_rh(station_prediction.rh_tgl_2, time_1800)
        rh_at_2100 = machine.predict_rh(station_prediction.rh_tgl_2, time_2100)
        station_prediction.bias_adjusted_rh = interpolate_between_two_points(
            18, 21, rh_at_1800, rh_at_2100, 20
        )

        # Predict the wind speed
        wind_speed_at_1800 = machine.predict_wind_speed(station_prediction.wind_tgl_10, time_1800)
        wind_speed_at_2100 = machine.predict_wind_speed(station_prediction.wind_tgl_10, time_2100)
        station_prediction.bias_adjusted_wind_speed = interpolate_between_two_points(
            18, 21, wind_speed_at_1800, wind_speed_at_2100, 20
        )

        # Predict the wind direction
        wind_direction_at_1800 = station_prediction.bias_adjusted_wdir = (
            machine.predict_wind_direction(
                station_prediction.wind_tgl_10,
                station_prediction.wdir_tgl_10,
                time_1800,
            )
        )
        wind_direction_at_2100 = station_prediction.bias_adjusted_wdir = (
            machine.predict_wind_direction(
                station_prediction.wind_tgl_10,
                station_prediction.wdir_tgl_10,
                time_2100,
            )
        )
        # Wind direction is circular (350 deg and 10 deg are only 20 deg apart), so a plain linear
        # interpolation would go the long way round. interpolate_bearing takes the shortest arc.
        # It needs datetimes (not hour numbers) because it interpolates over timestamps.
        station_prediction.bias_adjusted_wdir = interpolate_bearing(
            time_1800,
            time_2100,
            time_2000,
            wind_direction_at_1800,
            wind_direction_at_2100,
        )

        # Predict the 24h precipitation. No interpolation necessary due to the underlying model training.
        station_prediction.bias_adjusted_precip_24h = machine.predict_precipitation(
            station_prediction.precip_24h, station_prediction.prediction_timestamp
        )

    def _add_bias_adjustments_to_prediction(
        self, station_prediction: StationPrediction, machine: StationMachineLearning
    ):
        # Predict the temperature
        station_prediction.bias_adjusted_temperature = machine.predict_temperature(
            station_prediction.tmp_tgl_2, station_prediction.prediction_timestamp
        )

        # Predict the rh
        station_prediction.bias_adjusted_rh = machine.predict_rh(
            station_prediction.rh_tgl_2, station_prediction.prediction_timestamp
        )

        # Predict the wind speed
        station_prediction.bias_adjusted_wind_speed = machine.predict_wind_speed(
            station_prediction.wind_tgl_10, station_prediction.prediction_timestamp
        )

        # Predict the wind direction
        station_prediction.bias_adjusted_wdir = machine.predict_wind_direction(
            station_prediction.wind_tgl_10,
            station_prediction.wdir_tgl_10,
            station_prediction.prediction_timestamp,
        )

        # Predict the 24h precipitation
        station_prediction.bias_adjusted_precip_24h = machine.predict_precipitation(
            station_prediction.precip_24h, station_prediction.prediction_timestamp
        )

    def _process_prediction(
        self,
        prediction: ModelValues,
        station: WeatherStation,
        run_ts: datetime,
        machine: StationMachineLearning,
        prediction_is_interpolated: bool,
        station_predictions: dict[datetime, StationPrediction],
    ):
        """Add the station prediction for the model's values to station_predictions."""
        # If there's already a prediction, we want to update it
        station_prediction = station_predictions.get(prediction.prediction_timestamp)
        if station_prediction is None:
            station_prediction = StationPrediction()
        # Populate the weather station prediction object.
        station_prediction.station_code = station.code
        station_prediction.prediction_timestamp = prediction.prediction_timestamp
        # Calculate the interpolated values.
        # 2020 Dec 15, Sybrand: Encountered situation where tmp_tgl_2 was None, add this workaround for it.
        # NOTE: Not sure why this value would ever be None. This could happen if for whatever reason, the
        # tmp_tgl_2 layer failed to download and process, while other layers did.
        if prediction.tmp_tgl_2 is None:
            logger.warning(
                "tmp_tgl_2 is None for station %s at %s",
                station.code,
                prediction.prediction_timestamp,
            )
        else:
            temp = (
                prediction.tmp_tgl_2.item()
                if isinstance(prediction.tmp_tgl_2, np.float64)
                else prediction.tmp_tgl_2
            )
            station_prediction.tmp_tgl_2 = temp

        # 2020 Dec 10, Sybrand: Encountered situation where rh_tgl_2 was None, add this workaround for it.
        # NOTE: Not sure why this value would ever be None. This could happen if for whatever reason, the
        # rh_tgl_2 layer failed to download and process, while other layers did.
        if prediction.rh_tgl_2 is None:
            # This is unexpected, so we log it.
            logger.warning(
                "rh_tgl_2 is None for station %s at %s",
                station.code,
                prediction.prediction_timestamp,
            )
            station_prediction.rh_tgl_2 = None
        else:
            rh = (
                prediction.rh_tgl_2.item()
                if isinstance(prediction.rh_tgl_2, np.float64)
                else prediction.rh_tgl_2
            )
            station_prediction.rh_tgl_2 = rh
        # Check that apcp_sfc_0 is None, since accumulated precipitation
        # does not exist for 00 hour.
        if prediction.apcp_sfc_0 is None:
            station_prediction.apcp_sfc_0 = float(0.0)
        else:
            apcp = (
                prediction.apcp_sfc_0.item()
                if isinstance(prediction.apcp_sfc_0, np.float64)
                else prediction.apcp_sfc_0
            )
            station_prediction.apcp_sfc_0 = apcp
        # Calculate the delta_precipitation and 24 hour precip based on station's previous prediction_timestamp
        # for the same model run
        station_predictions[prediction.prediction_timestamp] = station_prediction
        station_prediction.precip_24h = self._calculate_past_24_hour_precip(
            station, run_ts, prediction, station_prediction, station_predictions
        )
        station_prediction.delta_precip = self._calculate_delta_precip(
            prediction, station_prediction, station_predictions
        )

        # Get the closest wind speed
        if prediction.wind_tgl_10 is not None:
            wind_tgl_10 = (
                prediction.wind_tgl_10.item()
                if isinstance(prediction.wind_tgl_10, np.float64)
                else prediction.wind_tgl_10
            )
            station_prediction.wind_tgl_10 = wind_tgl_10
        # Get the closest wind direcion
        if prediction.wdir_tgl_10 is not None:
            wdir_tgl_10 = (
                prediction.wdir_tgl_10.item()
                if isinstance(prediction.wdir_tgl_10, np.float64)
                else prediction.wdir_tgl_10
            )
            station_prediction.wdir_tgl_10 = wdir_tgl_10

        if prediction_is_interpolated:
            # Dealing with a numerical weather model that only has predictions at 3 hour intervals,
            # so no 20:00 UTC prediction available in the trained linear regression
            self._add_interpolated_bias_adjustments_to_prediction(station_prediction, machine)

        else:
            # No interpolation required
            self._add_bias_adjustments_to_prediction(station_prediction, machine)

        station_prediction.is_interpolated = prediction_is_interpolated

    def _calculate_past_24_hour_precip(
        self,
        station: WeatherStation,
        run_ts: datetime,
        prediction: ModelValues,
        station_prediction: StationPrediction,
        station_predictions: dict[datetime, StationPrediction],
    ):
        """Calculate the predicted precipitation over the previous 24 hours within the specified model run.
        If the model run does not contain a prediction timestamp for 24 hours prior to the current prediction,
        return the predicted precipitation from the previous run of the same model for the same time frame."""
        start_prediction_timestamp = prediction.prediction_timestamp - timedelta(days=1)
        # Check if a prediction exists for this model run 24 hours in the past
        previous_prediction_from_same_model_run = station_predictions.get(
            start_prediction_timestamp
        )
        # If a prediction from 24 hours ago from the same model run exists, return the difference in cumulative precipitation
        # between now and then as our total for the past 24 hours. We can end up with very very small negative numbers due
        # to floating point math, so return absolute value to avoid displaying -0.0.
        if previous_prediction_from_same_model_run is not None:
            return abs(
                station_prediction.apcp_sfc_0 - previous_prediction_from_same_model_run.apcp_sfc_0
            )

        # We're within 24 hours of the start of a model run so we don't have cumulative precipitation for a full 24h.
        # We use observed precipitation (ACTUALS in by_time) to make up the missing hours.
        # Each model run starts with a total precip of 0.0, so we need all the precip data
        # from 24 hours before the prediction_timestamp to the start of the current model run.
        actual_precip = get_accumulated_precipitation(
            self.observations,
            station.code,
            start_prediction_timestamp,
            run_ts,
        )
        return actual_precip + station_prediction.apcp_sfc_0

    def _calculate_delta_precip(
        self,
        prediction: ModelValues,
        station_prediction: StationPrediction,
        station_predictions: dict[datetime, StationPrediction],
    ):
        """Calculate the station_prediction's delta_precip based on the previous precip
        prediction for the station
        """
        previous_time = max(
            (time for time in station_predictions if time < prediction.prediction_timestamp),
            default=None,
        )
        # If there exists a previous prediction for the station from the same model run
        if previous_time is not None:
            return station_prediction.apcp_sfc_0 - station_predictions[previous_time].apcp_sfc_0
        # If there is no prior prediction within the same model run, it means that station_prediction is
        # the first prediction with apcp for the current model run (hour 001 or 003, depending on the
        # model type). In this case, delta_precip will be equal to the apcp
        return station_prediction.apcp_sfc_0

    def _process_model_run_for_station(
        self,
        run_ts: datetime,
        station: WeatherStation,
        predictions: list[ModelValues],
        history: ModelHistory,
    ) -> list[StationPrediction]:
        """Compute the station's predictions for the run, from the model's values at the station in
        time order."""
        # Extract the coordinate.
        coordinate = [station.long, station.lat]
        machine = StationMachineLearning(
            observations=self.observations,
            history=history,
            target_coordinate=coordinate,
            station_code=station.code,
            max_learn_date=run_ts,
        )
        machine.learn()

        station_predictions: dict[datetime, StationPrediction] = {}
        nam_cumulative_precip = 0.0
        # Iterate through all the predictions.
        prev_prediction = None

        for prediction in predictions:
            # NAM model requires manual calculation of cumulative precip
            if self.model_type == ModelEnum.NAM:
                nam_cumulative_precip, prediction.apcp_sfc_0 = accumulate_nam_precipitation(
                    nam_cumulative_precip, prediction, run_ts.hour
                )
            if (
                prev_prediction is not None
                and prev_prediction.prediction_timestamp.hour == 18
                and prediction.prediction_timestamp.hour == 21
            ):
                noon_prediction = construct_interpolated_noon_prediction(
                    prev_prediction, prediction, SCALAR_MODEL_VALUE_KEYS_FOR_INTERPOLATION
                )
                self._process_prediction(
                    noon_prediction, station, run_ts, machine, True, station_predictions
                )
            self._process_prediction(
                prediction, station, run_ts, machine, False, station_predictions
            )

            prev_prediction = prediction

        return [station_predictions[time] for time in sorted(station_predictions)]
