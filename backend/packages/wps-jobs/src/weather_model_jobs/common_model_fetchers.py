from typing import List
import logging
import numpy
from datetime import datetime, timedelta, timezone
from pyproj import Geod
import numpy as np
from sqlalchemy.orm import Session
from wps_shared import config
from wps_shared.db.crud.weather_models import (
    get_processed_file_record,
    get_processed_file_count,
    get_prediction_model_run_timestamp_records,
    get_model_run_predictions_for_station,
    get_weather_station_model_prediction,
    delete_model_run_predictions,
)
from weather_model_jobs.utils.interpolate import (
    construct_interpolated_noon_prediction,
    interpolate_between_two_points,
)
from weather_model_jobs.machine_learning import StationMachineLearning
from wps_shared.weather_models import ModelEnum
from wps_shared.schemas.stations import WeatherStation
from wps_shared.wps_logging import configure_logging
import wps_shared.utils.time as time_utils
from wps_shared.stations import get_stations_synchronously
from wps_shared.db.models.weather_models import (
    ProcessedModelRunUrl,
    PredictionModelRunTimestamp,
    WeatherStationModelPrediction,
    ModelRunPrediction,
)
import wps_shared.db.database
from wps_shared.db.crud.observations import get_accumulated_precipitation

# If running as its own process, configure logging appropriately.
if __name__ == "__main__":
    configure_logging()

logger = logging.getLogger(__name__)

# Keys for weather variables that require interpolation between 1800 and 2100
SCALAR_MODEL_VALUE_KEYS_FOR_INTERPOLATION = ("tmp_tgl_2", "rh_tgl_2", "wind_tgl_10", "apcp_sfc_0")


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


def flag_file_as_processed(url: str, session: Session):
    """Flag the file as processed in the database"""
    processed_file = get_processed_file_record(session, url)
    if processed_file:
        logger.info("re-processed %s", url)
    else:
        logger.info("file processed %s", url)
        processed_file = ProcessedModelRunUrl(url=url, create_date=time_utils.get_utc_now())
    processed_file.update_date = time_utils.get_utc_now()
    session.add(processed_file)
    session.commit()


def check_if_model_run_complete(session: Session, urls):
    """Check if a particular model run is complete"""
    actual_count = get_processed_file_count(session, urls)
    expected_count = len(urls)
    logger.info("we have processed %s/%s files", actual_count, expected_count)
    return actual_count == expected_count and actual_count > 0


def apply_data_retention_policy():
    """
    We can't keep data forever, we just don't have the space.
    """
    with wps_shared.db.database.get_write_session_scope() as session:
        # Weather station model predictions are partitioned and archived.
        # Model run predictions are used to inform weather station model predictions
        # and we can delete them over time by lessening data_retention_threshold.
        days_to_keep = int(config.get("DATA_RETENTION_THRESHOLD"))
        oldest_to_keep = time_utils.get_utc_now() - timedelta(days=days_to_keep)
        delete_model_run_predictions(session, oldest_to_keep)


def accumulate_nam_precipitation(
    nam_cumulative_precip: float, prediction: ModelRunPrediction, model_run_hour: int
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
    """Iterate through model runs that have completed, and calculate the interpolated weather predictions."""

    def __init__(self, session):
        """Prepare variables we're going to use throughout"""
        self.session = session
        self.stations = get_stations_synchronously()
        self.station_count = len(self.stations)

    def _process_model_run(self, model_run: PredictionModelRunTimestamp, model_type: ModelEnum):
        """Interpolate predictions in the provided model run for all stations."""
        logger.info("Interpolating values for model run: %s", model_run)
        # Iterate through stations.
        for index, station in enumerate(self.stations):
            logger.info(
                "Interpolating model run %s (%s/%s) for %s:%s",
                model_run.id,
                index,
                self.station_count,
                station.code,
                station.name,
            )
            # Process this model run for station.
            self._process_model_run_for_station(model_run, station, model_type)
        # Commit all the weather station model predictions (it's fast if we line them all up and commit
        # them in one go.)
        logger.info("commit to database...")
        self.session.commit()
        logger.info("done commit.")

    def _add_interpolated_bias_adjustments_to_prediction(
        self, station_prediction: WeatherStationModelPrediction, machine: StationMachineLearning
    ):
        # We need to interpolate prediction for 2000 using predictions for 1800 and 2100
        # Predict the temperature
        temp_at_1800 = machine.predict_temperature(
            station_prediction.tmp_tgl_2, station_prediction.prediction_timestamp.replace(hour=18)
        )
        temp_at_2100 = machine.predict_temperature(
            station_prediction.tmp_tgl_2, station_prediction.prediction_timestamp.replace(hour=21)
        )
        station_prediction.bias_adjusted_temperature = interpolate_between_two_points(
            18, 21, temp_at_1800, temp_at_2100, 20
        )
        # Predict the rh
        rh_at_1800 = machine.predict_rh(
            station_prediction.rh_tgl_2, station_prediction.prediction_timestamp.replace(hour=18)
        )
        rh_at_2100 = machine.predict_rh(
            station_prediction.rh_tgl_2, station_prediction.prediction_timestamp.replace(hour=21)
        )
        station_prediction.bias_adjusted_rh = interpolate_between_two_points(
            18, 21, rh_at_1800, rh_at_2100, 20
        )

        # Predict the wind speed
        wind_speed_at_1800 = machine.predict_wind_speed(
            station_prediction.wind_tgl_10, station_prediction.prediction_timestamp.replace(hour=18)
        )
        wind_speed_at_2100 = machine.predict_wind_speed(
            station_prediction.wind_tgl_10, station_prediction.prediction_timestamp.replace(hour=21)
        )
        station_prediction.bias_adjusted_wind_speed = interpolate_between_two_points(
            18, 21, wind_speed_at_1800, wind_speed_at_2100, 20
        )

        # Predict the wind direction
        wind_direction_at_1800 = station_prediction.bias_adjusted_wdir = (
            machine.predict_wind_direction(
                station_prediction.wind_tgl_10,
                station_prediction.wdir_tgl_10,
                station_prediction.prediction_timestamp.replace(hour=18),
            )
        )
        wind_direction_at_2100 = station_prediction.bias_adjusted_wdir = (
            machine.predict_wind_direction(
                station_prediction.wind_tgl_10,
                station_prediction.wdir_tgl_10,
                station_prediction.prediction_timestamp.replace(hour=21),
            )
        )
        station_prediction.bias_adjusted_wdir = interpolate_between_two_points(
            18, 21, wind_direction_at_1800, wind_direction_at_2100, 20
        )

        # Predict the 24h precipitation. No interpolation necessary due to the underlying model training.
        station_prediction.bias_adjusted_precip_24h = machine.predict_precipitation(
            station_prediction.precip_24h, station_prediction.prediction_timestamp
        )

    def _add_bias_adjustments_to_prediction(
        self, station_prediction: WeatherStationModelPrediction, machine: StationMachineLearning
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
        prediction: ModelRunPrediction,
        station: WeatherStation,
        model_run: PredictionModelRunTimestamp,
        machine: StationMachineLearning,
        prediction_is_interpolated: bool,
    ):
        """Create a WeatherStationModelPrediction from the ModelRunPrediction data."""
        # If there's already a prediction, we want to update it
        station_prediction = get_weather_station_model_prediction(
            self.session, station.code, model_run.id, prediction.prediction_timestamp
        )
        if station_prediction is None:
            station_prediction = WeatherStationModelPrediction()
        # Populate the weather station prediction object.
        station_prediction.station_code = station.code
        station_prediction.prediction_model_run_timestamp_id = model_run.id
        station_prediction.prediction_timestamp = prediction.prediction_timestamp
        # Calculate the interpolated values.
        # 2020 Dec 15, Sybrand: Encountered situation where tmp_tgl_2 was None, add this workaround for it.
        # NOTE: Not sure why this value would ever be None. This could happen if for whatever reason, the
        # tmp_tgl_2 layer failed to download and process, while other layers did.
        if prediction.tmp_tgl_2 is None:
            logger.warning("tmp_tgl_2 is None for ModelRunPrediction.id == %s", prediction.id)
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
            logger.warning("rh_tgl_2 is None for ModelRunPrediction.id == %s", prediction.id)
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
        self.session.flush()
        station_prediction.precip_24h = self._calculate_past_24_hour_precip(
            station, model_run, prediction, station_prediction
        )
        station_prediction.delta_precip = self._calculate_delta_precip(
            station, model_run, prediction, station_prediction
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

        # Update the update time (this might be an update)
        station_prediction.update_date = time_utils.get_utc_now()
        # Add this prediction to the session (we'll commit it later.)
        self.session.add(station_prediction)

    def _calculate_past_24_hour_precip(
        self,
        station: WeatherStation,
        model_run: PredictionModelRunTimestamp,
        prediction: ModelRunPrediction,
        station_prediction: WeatherStationModelPrediction,
    ):
        """Calculate the predicted precipitation over the previous 24 hours within the specified model run.
        If the model run does not contain a prediction timestamp for 24 hours prior to the current prediction,
        return the predicted precipitation from the previous run of the same model for the same time frame."""
        start_prediction_timestamp = prediction.prediction_timestamp - timedelta(days=1)
        # Check if a prediction exists for this model run 24 hours in the past
        previous_prediction_from_same_model_run = get_weather_station_model_prediction(
            self.session, station.code, model_run.id, start_prediction_timestamp
        )
        # If a prediction from 24 hours ago from the same model run exists, return the difference in cumulative precipitation
        # between now and then as our total for the past 24 hours. We can end up with very very small negative numbers due
        # to floating point math, so return absolute value to avoid displaying -0.0.
        if previous_prediction_from_same_model_run is not None:
            return abs(
                station_prediction.apcp_sfc_0 - previous_prediction_from_same_model_run.apcp_sfc_0
            )

        # We're within 24 hours of the start of a model run so we don't have cumulative precipitation for a full 24h.
        # We use actual precipitation from our API hourly_actuals table to make up the missing hours.
        # Each model run starts with a total precip of 0.0, so we need all the precip data
        # from 24 hours before the prediction_timestamp to the start of the current model run.
        actual_precip = get_accumulated_precipitation(
            self.session,
            station.code,
            start_prediction_timestamp,
            model_run.prediction_run_timestamp,
        )
        return actual_precip + station_prediction.apcp_sfc_0

    def _calculate_delta_precip(self, station, model_run, prediction, station_prediction):
        """Calculate the station_prediction's delta_precip based on the previous precip
        prediction for the station
        """
        results = (
            self.session.query(WeatherStationModelPrediction)
            .filter(WeatherStationModelPrediction.station_code == station.code)
            .filter(WeatherStationModelPrediction.prediction_model_run_timestamp_id == model_run.id)
            .filter(
                WeatherStationModelPrediction.prediction_timestamp < prediction.prediction_timestamp
            )
            .order_by(WeatherStationModelPrediction.prediction_timestamp.desc())
            .limit(1)
            .first()
        )
        # If there exists a previous prediction for the station from the same model run
        if results is not None:
            return station_prediction.apcp_sfc_0 - results.apcp_sfc_0
        # If there is no prior prediction within the same model run, it means that station_prediction is
        # the first prediction with apcp for the current model run (hour 001 or 003, depending on the
        # model type). In this case, delta_precip will be equal to the apcp
        return station_prediction.apcp_sfc_0

    def _process_model_run_for_station(
        self, model_run: PredictionModelRunTimestamp, station: WeatherStation, model_type: ModelEnum
    ):
        """Process the model run for the provided station."""
        # Extract the coordinate.
        coordinate = [station.long, station.lat]
        # Lookup the grid our weather station is in.
        logger.info(
            "Getting grid for coordinate %s and model %s", coordinate, model_run.prediction_model
        )
        machine = StationMachineLearning(
            session=self.session,
            model=model_run.prediction_model,
            target_coordinate=coordinate,
            station_code=station.code,
            max_learn_date=model_run.prediction_run_timestamp,
        )
        machine.learn()

        # Get all the predictions associated to this particular model run.
        query = get_model_run_predictions_for_station(self.session, station.code, model_run)

        nam_cumulative_precip = 0.0
        # Iterate through all the predictions.
        prev_prediction = None

        for prediction in query:
            # NAM model requires manual calculation of cumulative precip
            if model_type == ModelEnum.NAM:
                nam_cumulative_precip, prediction.apcp_sfc_0 = accumulate_nam_precipitation(
                    nam_cumulative_precip, prediction, model_run.prediction_run_timestamp.hour
                )
            if (
                prev_prediction is not None
                and prev_prediction.prediction_timestamp.hour == 18
                and prediction.prediction_timestamp.hour == 21
            ):
                noon_prediction = construct_interpolated_noon_prediction(
                    prev_prediction, prediction, SCALAR_MODEL_VALUE_KEYS_FOR_INTERPOLATION
                )
                self._process_prediction(noon_prediction, station, model_run, machine, True)
            self._process_prediction(prediction, station, model_run, machine, False)

            prev_prediction = prediction

    def _mark_model_run_interpolated(self, model_run: PredictionModelRunTimestamp):
        """Having completely processed a model run, we can mark it has having been interpolated."""
        model_run.interpolated = True
        logger.info("marking %s as interpolated", model_run)
        self.session.add(model_run)
        self.session.commit()

    def process(self, model_type: ModelEnum):
        """Entry point to start processing model runs that have not yet had their predictions interpolated"""
        # Get model runs that are complete (fully downloaded), but not yet interpolated.
        query = get_prediction_model_run_timestamp_records(
            self.session, complete=True, interpolated=False, model_type=model_type
        )
        for model_run, model in query:
            logger.info("model %s", model)
            logger.info("model_run %s", model_run)
            # Process the model run.
            start_time = datetime.now()
            self._process_model_run(model_run, model_type)
            # Mark the model run as interpolated.
            self._mark_model_run_interpolated(model_run)
            execution_time = datetime.now() - start_time
            logger.info(f"Interpolated & machine learned model run {model_run} in {execution_time}")
