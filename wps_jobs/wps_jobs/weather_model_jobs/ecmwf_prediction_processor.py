import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Dict, List

from wps_shared.db.crud.model_run_repository import ModelRunRepository
from wps_shared.db.models.weather_models import (
    ModelRunPrediction,
    PredictionModelRunTimestamp,
    WeatherStationModelPrediction,
)
from wps_shared.schemas.stations import WeatherStation

from wps_jobs.weather_model_jobs import ModelEnum
from wps_jobs.weather_model_jobs.machine_learning import StationMachineLearning
from wps_jobs.weather_model_jobs.utils.interpolate import (
    SCALAR_MODEL_VALUE_KEYS_FOR_INTERPOLATION,
    construct_interpolated_noon_prediction,
    interpolate_between_two_points,
)

logger = logging.getLogger(__name__)


class ECMWFPredictionProcessor:
    def __init__(self, stations: List[WeatherStation], model_run_repository: ModelRunRepository):
        self.stations = stations
        self.model_run_repository = model_run_repository
        self.station_predictions: Dict[int, List[ModelRunPrediction]] = defaultdict(list)

    def process(self):
        for (
            model_run,
            model,
        ) in self.model_run_repository.get_prediction_model_run_timestamp_records(
            complete=True, interpolated=False, model_type=ModelEnum.ECMWF
        ):
            logger.info("model %s", model)
            logger.info("model_run %s", model_run)
            # Process the model run.
            start_time = datetime.now()
            self._process_model_run(model_run)
            # Mark the model run as interpolated.
            self.model_run_repository.mark_model_run_interpolated(model_run)
            execution_time = datetime.now() - start_time
            logger.info(f"Interpolated & machine learned model run {model_run} in {execution_time}")

    def _process_model_run(self, model_run: PredictionModelRunTimestamp):
        """Interpolate predictions in the provided model run for all stations."""
        logger.info("Interpolating values for model run: %s", model_run)
        # Iterate through stations.
        for index, station in enumerate(self.stations):
            logger.info(
                "Interpolating model run %s (%s/%s) for %s:%s",
                model_run.id,
                index,
                len(self.stations),
                station.code,
                station.name,
            )
            # Process this model run for station.
            self._process_model_run_for_station(model_run, station)

    def _process_model_run_for_station(
        self, model_run: PredictionModelRunTimestamp, station: WeatherStation
    ):
        """Process the model run for the provided station."""
        # Extract the coordinate.
        coordinate = [station.long, station.lat]
        machine = StationMachineLearning(
            session=self.model_run_repository.session,
            model=model_run.prediction_model,
            target_coordinate=coordinate,
            station_code=station.code,
            max_learn_date=model_run.prediction_run_timestamp,
        )
        machine.learn()

        # Get all the predictions associated to this particular model run.
        model_run_predictions: List[ModelRunPrediction] = (
            self.model_run_repository.get_model_run_predictions_for_station(station.code, model_run)
        )

        # Iterate through all the predictions.
        prev_prediction: ModelRunPrediction | None = None

        for prediction in model_run_predictions:
            if prev_prediction is not None and self._should_interpolate(
                prev_prediction, prediction
            ):
                # create and store interpolated 20z prediction
                noon_prediction = construct_interpolated_noon_prediction(
                    prev_prediction, prediction, SCALAR_MODEL_VALUE_KEYS_FOR_INTERPOLATION
                )
                noon_station_prediction = self.initialize_station_prediction(
                    prev_prediction, noon_prediction
                )
                noon_station_prediction = self._apply_interpolated_bias_adjustments(
                    noon_station_prediction, prev_prediction, prediction, machine
                )
                self.model_run_repository.store_weather_station_model_prediction(
                    noon_station_prediction
                )

            # always process the current prediction
            station_prediction = self.initialize_station_prediction(prev_prediction, prediction)
            station_prediction = self._apply_bias_adjustments(station_prediction, machine)
            self.model_run_repository.store_weather_station_model_prediction(station_prediction)

            prev_prediction = prediction

    def _should_interpolate(
        self, prev_prediction: ModelRunPrediction, prediction: ModelRunPrediction
    ) -> bool:
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

    def _weather_station_prediction_initializer(
        self, prediction: ModelRunPrediction
    ) -> WeatherStationModelPrediction:
        """Initialize a WeatherStationModelPrediction object."""

        station_prediction = self.model_run_repository.get_weather_station_model_prediction(
            prediction.station_code,
            prediction.prediction_model_run_timestamp_id,
            prediction.prediction_timestamp,
        )

        if station_prediction is None:
            station_prediction = WeatherStationModelPrediction()
            station_prediction.station_code = prediction.station_code
            station_prediction.prediction_model_run_timestamp_id = (
                prediction.prediction_model_run_timestamp_id
            )
            station_prediction.prediction_timestamp = prediction.prediction_timestamp

        return station_prediction

    def _apply_interpolated_bias_adjustments(
        self,
        station_prediction: WeatherStationModelPrediction,
        prev_prediction: ModelRunPrediction,
        prediction: ModelRunPrediction,
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
        self, station_prediction: WeatherStationModelPrediction, machine: StationMachineLearning
    ):
        """Create a WeatherStationModelPrediction from the ModelRunPrediction data."""
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
        self, prev_prediction: ModelRunPrediction, prediction: ModelRunPrediction
    ) -> WeatherStationModelPrediction:
        """Initialize a WeatherStationModelPrediction object with the provided prediction data."""
        station_prediction = self._weather_station_prediction_initializer(prediction)
        station_prediction.tmp_tgl_2 = prediction.get_temp()
        station_prediction.rh_tgl_2 = prediction.get_rh()
        station_prediction.apcp_sfc_0 = prediction.get_precip()

        station_prediction.precip_24h = self._calculate_past_24_hour_precip(
            prediction, station_prediction
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
        self, prediction: ModelRunPrediction, station_prediction: WeatherStationModelPrediction
    ):
        """Calculate the predicted precipitation over the previous 24 hours within the specified model run.
        If the model run does not contain a prediction timestamp for 24 hours prior to the current prediction,
        return the predicted precipitation from the previous run of the same model for the same time frame."""
        start_prediction_timestamp: datetime = prediction.prediction_timestamp - timedelta(days=1)
        # Check if a prediction exists for this model run 24 hours in the past
        previous_prediction_from_same_model_run = (
            self.model_run_repository.get_weather_station_model_prediction(
                prediction.station_code,
                prediction.prediction_model_run_timestamp_id,
                start_prediction_timestamp,
            )
        )
        # If a prediction from 24 hours ago from the same model run exists, return the difference in cumulative precipitation
        # between now and then as our total for the past 24 hours. We can end up with very very small negative numbers due
        # to floating point math, so return absolute value to avoid displaying -0.0.
        if previous_prediction_from_same_model_run is not None:
            return abs(
                station_prediction.apcp_sfc_0 - previous_prediction_from_same_model_run.apcp_sfc_0
            )

        # We're within 24 hours of the start of a model run so we don't have cumulative precipitation for a full 24h.
        # We use actual precipitation from our hourly_actuals table to make up the missing hours.
        prediction_timestamp: datetime = station_prediction.prediction_timestamp
        # Create new datetime with time of 00:00 hours as the end time.
        end_prediction_timestamp = datetime(
            year=prediction_timestamp.year,
            month=prediction_timestamp.month,
            day=prediction_timestamp.day,
            tzinfo=timezone.utc,
        )
        actual_precip = self.model_run_repository.get_accumulated_precipitation(
            prediction.station_code, start_prediction_timestamp, end_prediction_timestamp
        )
        return actual_precip + station_prediction.apcp_sfc_0

    def _calculate_delta_precip(
        self, prev_prediction: ModelRunPrediction, station_prediction: WeatherStationModelPrediction
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
