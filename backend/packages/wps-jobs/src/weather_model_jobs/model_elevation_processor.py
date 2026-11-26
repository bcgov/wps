"""Store model surface elevations for Morecast weather stations."""

import logging
import tempfile
from pathlib import Path
from time import perf_counter

from sqlalchemy.orm import Session
from weather_model_jobs.model_elevation_sampler import ModelElevationSampler
from wps_shared.db.crud.weather_models import (
    get_model_run_elevation_station_codes,
    get_model_run_station_codes,
    get_prediction_model_run_timestamp_records,
    store_model_run_station_elevations,
)
from wps_shared.db.models.weather_models import PredictionModelRunTimestamp
from wps_shared.schemas.stations import WeatherStation
from wps_shared.weather_models import ModelEnum

logger = logging.getLogger(__name__)


class ModelElevationProcessor:
    """Store model surface elevations at weather station locations.

    Use the same grid cells as the weather forecasts, and save one elevation in metres per station
    and model run. All forecast hours share that value.
    """

    def __init__(self, session: Session, stations: list[WeatherStation]) -> None:
        self.session = session
        self.stations = stations

    def process(self, model_type: ModelEnum) -> None:
        """Download and store model surface elevations for stations with forecasts.

        Process pending runs of the requested model. Surface files are temporary.
        Only the sampled station elevations are kept.
        """
        if model_type == ModelEnum.NAM:
            return
        runs = get_prediction_model_run_timestamp_records(
            self.session, model_type=model_type, complete=True, interpolated=False
        ).all()
        if not runs:
            logger.debug("No pending runs for station elevations model=%s", model_type.value)
            return
        with tempfile.TemporaryDirectory(prefix="wps-station-elevation-") as directory:
            elevation_sampler = ModelElevationSampler(Path(directory))
            for run, _ in runs:
                # a failed flush can expire ORM attributes needed for the error context
                model_run_timestamp = run.prediction_run_timestamp.isoformat()
                try:
                    self.process_run(run, model_type.value, elevation_sampler)
                except Exception as error:
                    # the existing ChatOps handler includes exception notes in its traceback
                    error.add_note(
                        f"Station elevation processing failed for {model_type.value} "
                        f"initialization {model_run_timestamp}"
                    )
                    raise

    def process_run(
        self, run: PredictionModelRunTimestamp, model: str, elevation_sampler: ModelElevationSampler
    ) -> None:
        """Store missing model elevations for stations with predictions in this run.

        Keep existing entries and skip unavailable elevations. Missing station
        metadata or failed downloads and samples shouldn't block the forecast interpolation.
        """
        model_run_timestamp = run.prediction_run_timestamp.isoformat()
        station_codes = get_model_run_station_codes(self.session, run.id)
        existing_codes = get_model_run_elevation_station_codes(self.session, run.id)
        missing = station_codes - existing_codes
        if not missing:
            logger.debug(
                "Skipping station elevations model=%s initialization=%s: no missing assignments",
                model,
                model_run_timestamp,
            )
            return
        started = perf_counter()
        logger.info(
            "Processing station elevations model=%s initialization=%s pending=%s existing=%s",
            model,
            model_run_timestamp,
            len(missing),
            len(station_codes) - len(missing),
        )
        stations = [station for station in self.stations if station.code in missing]
        elevations = {}
        if stations:
            try:
                elevations = elevation_sampler.download_and_sample(
                    model, run.prediction_run_timestamp, stations
                )
            except Exception:
                # optional metadata must not block forecast interpolation
                logger.exception(
                    "Station elevation sampling failed model=%s initialization=%s; "
                    "skipping unavailable elevations",
                    model,
                    model_run_timestamp,
                )
        store_model_run_station_elevations(self.session, run.id, missing, elevations)

        matched_codes = {station.code for station in stations}
        missing_metadata_codes = sorted(missing - matched_codes)
        missing_sample_codes = sorted(
            code for code in matched_codes if elevations.get(code) is None
        )
        unavailable_count = len(missing_metadata_codes) + len(missing_sample_codes)
        logger.info(
            "Station elevations processed model=%s initialization=%s "
            "flushed=%s available=%s unavailable=%s elapsed_seconds=%.2f",
            model,
            model_run_timestamp,
            len(missing) - unavailable_count,
            len(missing) - unavailable_count,
            unavailable_count,
            perf_counter() - started,
        )
        if missing_metadata_codes:
            logger.warning(
                "Station metadata unavailable model=%s initialization=%s station_codes=%s",
                model,
                model_run_timestamp,
                missing_metadata_codes,
            )
        if missing_sample_codes:
            logger.warning(
                "Model elevation samples unavailable model=%s initialization=%s station_codes=%s",
                model,
                model_run_timestamp,
                missing_sample_codes,
            )
