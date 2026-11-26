import logging
from collections.abc import Iterable
from datetime import datetime, timedelta
from typing import List

from weather_model_jobs import ModelEnum
from weather_model_jobs.common_model_fetchers import finish_interrupted_publish
from weather_model_jobs.ecmwf_hours import get_ecmwf_forecast_hours
from weather_model_jobs.machine_learning import (
    StationMachineLearning,
    read_model_history,
    read_observations,
)
from weather_model_jobs.model_history import ModelHistory
from weather_model_jobs.model_values import ModelValues, StationPrediction
from weather_model_jobs.utils.interpolate import (
    SCALAR_MODEL_VALUE_KEYS_FOR_INTERPOLATION,
    construct_interpolated_noon_prediction,
    interpolate_between_two_points,
)
from wps_shared.schemas.stations import WeatherStation
from wps_weather_data.actuals import StationObservations, get_accumulated_precipitation
from wps_weather_data.by_time import ByTimeTable
from wps_weather_data.runs import RunsTable
from wps_weather_data.staging import StagingTable

logger = logging.getLogger(__name__)


class ECMWFPredictionProcessor:
    """Turn fully staged ECMWF runs into station predictions, and publish them."""

    def __init__(
        self,
        stations: List[WeatherStation],
        runs_table: RunsTable | None = None,
        by_time_table: ByTimeTable | None = None,
        staging_table: StagingTable | None = None,
    ):
        self.stations = stations
        self.runs_table = runs_table or RunsTable()
        self.by_time_table = by_time_table or ByTimeTable()
        self.staging_table = staging_table or StagingTable(ModelEnum.ECMWF)
        # The observations for the run being published: read once per run, for training and for
        # the observed precip that a run's first day of 24 hour precip adds.
        self.observations = StationObservations({})

    def process(self, run_timestamps: Iterable[datetime]):
        """Publish each of the runs, which must be fully staged."""
        for run_ts in run_timestamps:
            start_time = datetime.now()
            self.publish_run(run_ts)
            execution_time = datetime.now() - start_time
            logger.info(f"Interpolated & machine learned model run {run_ts} in {execution_time}")

    def publish_run(self, run_ts: datetime):
        """Compute a staged run's station predictions, append them to `runs`, merge them into
        `by_time`, then delete the run from `staging`."""
        if finish_interrupted_publish(
            self.runs_table, self.by_time_table, self.staging_table, ModelEnum.ECMWF, run_ts
        ):
            return
        logger.info("Interpolating values for model run: %s", run_ts)
        staged = self.staging_table.station_values(run_ts)
        history = read_model_history(self.runs_table, ModelEnum.ECMWF, run_ts)
        self.observations = read_observations(self.by_time_table, run_ts)
        rows = []
        for index, station in enumerate(self.stations):
            logger.info(
                "Interpolating model run %s (%s/%s) for %s:%s",
                run_ts,
                index,
                len(self.stations),
                station.code,
                station.name,
            )
            predictions = [
                ModelValues.from_staging(station.code, values)
                for values in staged.get(station.code, [])
            ]
            station_predictions = self._process_model_run_for_station(
                run_ts, station, predictions, history
            )
            rows.extend(prediction.as_row() for prediction in station_predictions)
        if not rows:
            # Kept in staging: deleting it would make the next run download it all again.
            logger.error(
                "No station predictions for %s model run %s, leaving it in staging",
                ModelEnum.ECMWF.value,
                run_ts,
            )
            return
        self.runs_table.append_run(ModelEnum.ECMWF, run_ts, rows)
        self.by_time_table.merge_run(ModelEnum.ECMWF, run_ts, rows)
        self.staging_table.delete_run(run_ts)

    def _process_model_run_for_station(
        self,
        run_ts: datetime,
        station: WeatherStation,
        model_run_predictions: List[ModelValues],
        history: ModelHistory,
    ) -> List[StationPrediction]:
        """Compute the station's predictions for the run, from the model's values at the station in
        time order."""
        if not self._has_expected_timestamp_coverage(run_ts, station, model_run_predictions):
            return []

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
        # Iterate through all the predictions.
        prev_prediction: ModelValues | None = None

        for prediction in model_run_predictions:
            if prev_prediction is not None and self._should_interpolate(
                prev_prediction, prediction
            ):
                # create and store interpolated 20z prediction
                noon_prediction = construct_interpolated_noon_prediction(
                    prev_prediction, prediction, SCALAR_MODEL_VALUE_KEYS_FOR_INTERPOLATION
                )
                noon_station_prediction = self.initialize_station_prediction(
                    prev_prediction, noon_prediction, run_ts, station_predictions
                )
                noon_station_prediction = self._apply_interpolated_bias_adjustments(
                    noon_station_prediction, prev_prediction, prediction, machine
                )
                noon_station_prediction.is_interpolated = True
                station_predictions[noon_prediction.prediction_timestamp] = noon_station_prediction

            # always process the current prediction
            station_prediction = self.initialize_station_prediction(
                prev_prediction, prediction, run_ts, station_predictions
            )
            station_prediction = self._apply_bias_adjustments(station_prediction, machine)
            station_predictions[prediction.prediction_timestamp] = station_prediction

            prev_prediction = prediction

        return [station_predictions[time] for time in sorted(station_predictions)]

    @staticmethod
    def _has_expected_timestamp_coverage(
        run_ts: datetime,
        station: WeatherStation,
        predictions: List[ModelValues],
    ) -> bool:
        expected_timestamps = {
            run_ts + timedelta(hours=hour) for hour in get_ecmwf_forecast_hours()
        }
        actual_timestamps = {prediction.prediction_timestamp for prediction in predictions}
        missing_timestamps = expected_timestamps - actual_timestamps
        unexpected_timestamps = actual_timestamps - expected_timestamps

        if not missing_timestamps and not unexpected_timestamps:
            return True

        logger.error(
            "Skipping incomplete ECMWF predictions for model run %s, station %s:%s: "
            "expected=%s, actual=%s, missing=%s, unexpected=%s",
            run_ts,
            station.code,
            station.name,
            len(expected_timestamps),
            len(actual_timestamps),
            len(missing_timestamps),
            len(unexpected_timestamps),
        )
        return False

    def _should_interpolate(self, prev_prediction: ModelValues, prediction: ModelValues) -> bool:
        """Check if we should interpolate between the two predictions."""
        prev_timestamp: datetime = prev_prediction.prediction_timestamp
        next_timestamp: datetime = prediction.prediction_timestamp
        assert next_timestamp > prev_timestamp, (
            "Next timestamp must be greater than previous timestamp"
        )
        # Assert the hour difference is 24 or less
        assert (next_timestamp - prev_timestamp).total_seconds() <= 24 * 3600, (
            "Timestamps must be no more than 24 hours apart"
        )
        # Check if datetimes are on the same day
        if prev_timestamp.date() == next_timestamp.date():
            # Timestamps on the same day but surround 20:00 UTC should be interpolated
            return prev_timestamp.hour < 20 and next_timestamp.hour > 20

        # datetimes are on different days, interpolate if previous is before 20:00 UTC
        return prev_timestamp.hour < 20

    def _apply_interpolated_bias_adjustments(
        self,
        station_prediction: StationPrediction,
        prev_prediction: ModelValues,
        prediction: ModelValues,
        machine: StationMachineLearning,
    ):
        prev_prediction_datetime: datetime = prev_prediction.prediction_timestamp
        prediction_datetime: datetime = prediction.prediction_timestamp
        datetime_at_2000 = prev_prediction_datetime.replace(hour=20)

        temp_before_2000 = machine.predict_temperature(
            station_prediction.tmp_tgl_2, prev_prediction_datetime
        )
        temp_after_2000 = machine.predict_temperature(
            station_prediction.tmp_tgl_2, prediction_datetime
        )
        station_prediction.bias_adjusted_temperature = self.interpolate_20_00_values(
            prev_prediction_datetime,
            prediction_datetime,
            temp_before_2000,
            temp_after_2000,
            datetime_at_2000,
        )

        rh_before_2000 = machine.predict_rh(station_prediction.rh_tgl_2, prev_prediction_datetime)
        rh_after_2000 = machine.predict_rh(station_prediction.rh_tgl_2, prediction_datetime)
        station_prediction.bias_adjusted_rh = self.interpolate_20_00_values(
            prev_prediction_datetime,
            prediction_datetime,
            rh_before_2000,
            rh_after_2000,
            datetime_at_2000,
        )

        wind_speed_before_2000 = machine.predict_wind_speed(
            station_prediction.wind_tgl_10, prev_prediction_datetime
        )
        wind_speed_after_2000 = machine.predict_wind_speed(
            station_prediction.wind_tgl_10, prediction_datetime
        )
        station_prediction.bias_adjusted_wind_speed = self.interpolate_20_00_values(
            prev_prediction_datetime,
            prediction_datetime,
            wind_speed_before_2000,
            wind_speed_after_2000,
            datetime_at_2000,
        )

        wind_direction_before_2000 = station_prediction.bias_adjusted_wdir = (
            machine.predict_wind_direction(
                station_prediction.wind_tgl_10,
                station_prediction.wdir_tgl_10,
                prev_prediction_datetime,
            )
        )
        wind_direction_after_2000 = station_prediction.bias_adjusted_wdir = (
            machine.predict_wind_direction(
                station_prediction.wind_tgl_10,
                station_prediction.wdir_tgl_10,
                prediction_datetime,
            )
        )
        station_prediction.bias_adjusted_wdir = self.interpolate_20_00_values(
            prev_prediction_datetime,
            prediction_datetime,
            wind_direction_before_2000,
            wind_direction_after_2000,
            datetime_at_2000,
        )

        # Predict the 24h precipitation. No interpolation necessary due to the underlying model training.
        station_prediction.bias_adjusted_precip_24h = machine.predict_precipitation(
            station_prediction.precip_24h, station_prediction.prediction_timestamp
        )
        return station_prediction

    def _apply_bias_adjustments(
        self, station_prediction: StationPrediction, machine: StationMachineLearning
    ):
        """Create a StationPrediction from the ModelValues data."""
        station_prediction.bias_adjusted_temperature = machine.predict_temperature(
            station_prediction.tmp_tgl_2, station_prediction.prediction_timestamp
        )
        station_prediction.bias_adjusted_rh = machine.predict_rh(
            station_prediction.rh_tgl_2, station_prediction.prediction_timestamp
        )
        station_prediction.bias_adjusted_wind_speed = machine.predict_wind_speed(
            station_prediction.wind_tgl_10, station_prediction.prediction_timestamp
        )
        station_prediction.bias_adjusted_wdir = machine.predict_wind_direction(
            station_prediction.wind_tgl_10,
            station_prediction.wdir_tgl_10,
            station_prediction.prediction_timestamp,
        )
        station_prediction.bias_adjusted_precip_24h = machine.predict_precipitation(
            station_prediction.precip_24h, station_prediction.prediction_timestamp
        )
        return station_prediction

    def initialize_station_prediction(
        self,
        prev_prediction: ModelValues | None,
        prediction: ModelValues,
        run_ts: datetime,
        station_predictions: dict[datetime, StationPrediction],
    ) -> StationPrediction:
        """Initialize a StationPrediction object with the provided prediction data."""
        station_prediction = station_predictions.get(prediction.prediction_timestamp)
        if station_prediction is None:
            station_prediction = StationPrediction(
                station_code=prediction.station_code,
                prediction_timestamp=prediction.prediction_timestamp,
            )
        station_prediction.tmp_tgl_2 = prediction.get_temp()
        station_prediction.rh_tgl_2 = prediction.get_rh()
        station_prediction.apcp_sfc_0 = prediction.get_precip()

        station_prediction.precip_24h = self._calculate_past_24_hour_precip(
            prediction, station_prediction, run_ts, station_predictions
        )
        station_prediction.delta_precip = self._calculate_delta_precip(
            prev_prediction, station_prediction
        )

        station_prediction.wind_tgl_10 = prediction.get_wind_speed()
        station_prediction.wdir_tgl_10 = prediction.get_wind_direction()
        return station_prediction

    def interpolate_20_00_values(
        self,
        prev_datetime: datetime,
        next_datetime: datetime,
        prev_value: float,
        next_value: float,
        target_datetime: datetime,
    ) -> float | None:
        """Interpolate the value at 2000 UTC using the previous and next values."""
        assert target_datetime.hour == 20, "Target datetime must be at 20:00 UTC"
        assert prev_datetime < target_datetime, "Previous datetime must be before target datetime"
        assert next_datetime > target_datetime, "Next datetime must be after target datetime"
        # Interpolate the value at 2000 UTC
        return interpolate_between_two_points(
            int(prev_datetime.timestamp()),
            int(next_datetime.timestamp()),
            prev_value,
            next_value,
            int(target_datetime.timestamp()),
        )

    def _calculate_past_24_hour_precip(
        self,
        prediction: ModelValues,
        station_prediction: StationPrediction,
        run_ts: datetime,
        station_predictions: dict[datetime, StationPrediction],
    ):
        """Calculate the predicted precipitation over the previous 24 hours within the specified model run.
        If the model run does not contain a prediction timestamp for 24 hours prior to the current prediction,
        return the predicted precipitation from the previous run of the same model for the same time frame."""
        start_prediction_timestamp: datetime = prediction.prediction_timestamp - timedelta(days=1)
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
            prediction.station_code,
            start_prediction_timestamp,
            run_ts,
        )
        return actual_precip + station_prediction.apcp_sfc_0

    def _calculate_delta_precip(
        self, prev_prediction: ModelValues | None, station_prediction: StationPrediction
    ):
        """Calculate the station_prediction's delta_precip based on the previous precip
        prediction for the station
        """
        if prev_prediction is not None:
            return station_prediction.apcp_sfc_0 - prev_prediction.apcp_sfc_0
        # If there is no prior prediction within the same model run, it means that station_prediction is
        # the first prediction with apcp for the current model run (hour 001 or 003, depending on the
        # model type). In this case, delta_precip will be equal to the apcp
        return station_prediction.apcp_sfc_0
