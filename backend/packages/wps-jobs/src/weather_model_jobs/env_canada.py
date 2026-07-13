"""A script that downloads weather models from Environment Canada HTTP data server
https://app.zenhub.com/workspaces/wildfire-predictive-services-5e321393e038fba5bbe203b8/issues/bcgov/wps/1601
"""

import datetime
import logging
import os
import sys
import tempfile
from urllib.parse import urlparse

import requests
import wps_shared.db.database
import wps_shared.utils.time as time_utils
from sqlalchemy.orm import Session
from weather_model_jobs.common_model_fetchers import (
    ModelValueProcessor,
    apply_data_retention_policy,
    check_if_model_run_complete,
    flag_file_as_processed,
)
from weather_model_jobs.utils.process_grib import (
    GribFileProcessor,
    ModelRunInfo,
)
from wps_shared.chatops_notification import send_chatops_notification
from wps_shared.db.crud.weather_models import (
    get_prediction_model,
    get_prediction_run,
    get_processed_file_record,
    update_prediction_run,
)
from wps_shared.weather_models import (
    CompletedWithSomeExceptions,
    ModelEnum,
    NoFilesProcessed,
    ProjectionEnum,
    UnhandledPredictionModelType,
    adjust_model_day,
    download,
    get_env_canada_model_run_hours,
)
from wps_shared.weather_models.eccc_url_fetcher import ECCCUrlFetcher
from wps_shared.weather_models.model_run_urls import (
    get_model_run_urls,
)
from wps_shared.wps_logging import configure_logging

# If running as its own process, configure logging appropriately.
if __name__ == "__main__":
    configure_logging()

logger = logging.getLogger(__name__)


def parse_gdps_msc_filename(url: str):
    """Parse MSC GDPS filename format.

    Expected:
    {YYYYMMDD}T{HH}Z_MSC_GDPS_{VAR_LEVEL}_LatLon0.15_PT{hhh}H.grib2

    Example:
    20260501T12Z_MSC_GDPS_TMP_AGL-2m_LatLon0.15_PT003H.grib2
    """

    base = os.path.basename(url)

    try:
        run_part, provider, model, remainder = base.split("_", 3)
    except ValueError as exc:
        raise ValueError(f"Not a valid MSC GDPS filename: {base}") from exc

    if provider != "MSC" or model != "GDPS":
        raise ValueError(f"Not a valid MSC GDPS filename: {base}")

    try:
        variable_name, projection_part, forecast_part = remainder.rsplit("_", 2)
    except ValueError as exc:
        raise ValueError(f"Not a valid MSC GDPS filename: {base}") from exc

    if projection_part != "LatLon0.15":
        raise ValueError(f"Unsupported projection in filename: {projection_part}")

    if not forecast_part.endswith(".grib2"):
        raise ValueError(f"Expected .grib2 filename: {base}")

    forecast_part = forecast_part.removesuffix(".grib2")

    if not forecast_part.startswith("PT") or not forecast_part.endswith("H"):
        raise ValueError(f"Cannot parse forecast hour from: {forecast_part}")

    try:
        model_run_timestamp = datetime.datetime.strptime(
            run_part,
            "%Y%m%dT%HZ",
        ).replace(tzinfo=datetime.timezone.utc)

        forecast_hours = int(forecast_part.removeprefix("PT").removesuffix("H"))
    except ValueError as exc:
        raise ValueError(f"Cannot parse timestamps from filename: {base}") from exc

    prediction_timestamp = model_run_timestamp + datetime.timedelta(hours=forecast_hours)

    return (
        variable_name,
        ProjectionEnum.LATLON_15X_15,
        model_run_timestamp,
        prediction_timestamp,
    )


def parse_rdps_msc_filename(url: str):
    """Parse the new MSC RDPS filename format.

    Expected filename: {YYYYMMDD}T{HH}Z_MSC_RDPS_{VAR_LEVEL}_RLatLon0.09_PT{hhh}H.grib2
    Example: 20260501T12Z_MSC_RDPS_TMP_AGL-2m_RLatLon0.09_PT003H.grib2
    Returns: (variable_name, ProjectionEnum.RDPS_LATLON, model_run_timestamp, prediction_timestamp)
    """

    basename = os.path.basename(url)
    parts = basename.split("_")
    # parts[0] = "20260501T12Z", parts[1] = "MSC", parts[2] = "RDPS"
    if len(parts) < 6 or parts[1] != "MSC" or parts[2] != "RDPS":
        raise ValueError(f"Not a valid MSC RDPS filename: {basename}")

    date_run = parts[0]  # e.g. "20260501T12Z"
    if len(date_run) != 12 or "T" not in date_run:
        raise ValueError(f"Cannot parse date/run from: {date_run}")

    date_str = date_run[:8]  # "20260501"
    run_hour = int(date_run[9:11])  # 12

    model_run_timestamp = datetime.datetime(
        year=int(date_str[:4]),
        month=int(date_str[4:6]),
        day=int(date_str[6:8]),
        hour=run_hour,
        tzinfo=datetime.timezone.utc,
    )

    # Variable name: everything between "_RDPS_" and "_RLatLon"
    after_rdps = basename[basename.index("_RDPS_") + 6 :]
    variable_name = after_rdps[: after_rdps.index("_RLatLon")]

    # Forecast hour from last part: "PT003H.grib2" -> 3
    pt_part = parts[-1].split(".")[0]  # "PT003H"
    if not pt_part.startswith("PT") or not pt_part.endswith("H"):
        raise ValueError(f"Cannot parse forecast hour from: {pt_part}")
    forecast_hours = int(pt_part[2:-1])
    prediction_timestamp = model_run_timestamp + datetime.timedelta(hours=forecast_hours)

    return variable_name, ProjectionEnum.RDPS_LATLON, model_run_timestamp, prediction_timestamp


def parse_high_res_model_url(url):
    """Parse filename for HRDPS grib file to extract metadata"""
    base = os.path.basename(url)
    base_parts = base.split("_")
    url_parts = url.split("/")
    try:
        variable = base_parts[3]
        level = base_parts[4]
        variable_name = "_".join([variable, level])
        projection = ProjectionEnum.HRDPS_LATLON
        run_date_str = base_parts[0][:-4]
        run_hour_str = url_parts[7]
        model_run_timestamp = datetime.datetime(
            year=int(run_date_str[:4]),
            month=int(run_date_str[4:6]),
            day=int(run_date_str[6:8]),
            hour=int(run_hour_str),
            tzinfo=datetime.timezone.utc,
        )
        prediction_hour = url_parts[8]
        prediction_timestamp = model_run_timestamp + datetime.timedelta(hours=int(prediction_hour))
        return variable_name, projection, model_run_timestamp, prediction_timestamp
    except (IndexError, ValueError) as exception:
        logger.exception("HRDPS URL %s is not in the expected format", url)
        raise ValueError(f"HRDPS URL {url} is not in the expected format") from exception


def parse_env_canada_filename(url):
    """Take a grib url, as per file name nomenclature defined at
    https://eccc-msc.github.io/open-data/readme_en/, and parse into a meaningful object.
    """
    filename = os.path.basename(urlparse(url).path)
    base = os.path.basename(filename)
    parts = base.split("_")
    if "GDPS" in parts:
        variable_name, projection, model_run_timestamp, prediction_timestamp = (
            parse_gdps_msc_filename(url)
        )
        model_enum = ModelEnum.GDPS
    elif "HRDPS" in parts:
        variable_name, projection, model_run_timestamp, prediction_timestamp = (
            parse_high_res_model_url(url)
        )
        model_enum = ModelEnum.HRDPS
    elif "RDPS" in parts:
        variable_name, projection, model_run_timestamp, prediction_timestamp = (
            parse_rdps_msc_filename(url)
        )
        model_enum = ModelEnum.RDPS
    else:
        raise UnhandledPredictionModelType("Unhandled prediction model type found", filename)

    info = ModelRunInfo()
    info.model_enum = model_enum
    info.projection = projection
    info.model_run_timestamp = model_run_timestamp
    info.prediction_timestamp = prediction_timestamp
    info.variable_name = variable_name
    return info


def mark_prediction_model_run_processed(
    session: Session,
    model: ModelEnum,
    projection: ProjectionEnum,
    now: datetime.datetime,
    model_run_hour: int,
):
    """Mark a prediction model run as processed (complete)"""

    prediction_model = get_prediction_model(session, model, projection)
    prediction_run_timestamp = datetime.datetime(
        year=now.year, month=now.month, day=now.day, hour=now.hour, tzinfo=datetime.timezone.utc
    )
    prediction_run_timestamp = adjust_model_day(prediction_run_timestamp, model_run_hour)
    prediction_run_timestamp = prediction_run_timestamp.replace(hour=model_run_hour)
    logger.info(
        "prediction_model:%s, prediction_run_timestamp:%s",
        prediction_model,
        prediction_run_timestamp,
    )
    prediction_run = get_prediction_run(session, prediction_model.id, prediction_run_timestamp)
    logger.info("prediction run: %s", prediction_run)
    prediction_run.complete = True
    update_prediction_run(session, prediction_run)


class EnvCanada:
    """Class that orchestrates downloading and processing of weather model grib files from environment
    Canada.
    """

    def __init__(self, session: Session, model_type: ModelEnum):
        """Prep variables"""
        self.files_downloaded = 0
        self.files_processed = 0
        self.exception_count = 0
        self.connection_error_count = 0
        # We always work in UTC:
        self.now = time_utils.get_utc_now()
        self.grib_processor = GribFileProcessor()
        self.model_type: ModelEnum = model_type
        self.session = session
        # set projection based on model_type
        if self.model_type == ModelEnum.GDPS:
            self.projection = ProjectionEnum.LATLON_15X_15
        elif self.model_type == ModelEnum.HRDPS:
            self.projection = ProjectionEnum.HRDPS_LATLON
        elif self.model_type == ModelEnum.RDPS:
            self.projection = ProjectionEnum.RDPS_LATLON
        else:
            raise UnhandledPredictionModelType(f"Unknown model type: {self.model_type}")

    def process_model_run_urls(self, urls, fetcher: ECCCUrlFetcher):
        """Process the urls for a model run."""
        for url in urls:
            try:
                # check the database for a record of this file:
                processed_file_record = get_processed_file_record(self.session, url)
                if processed_file_record:
                    # This file has already been processed - so we skip it.
                    # NOTE: changing this to logger.debug causes too much noise in unit tests.
                    logger.debug("file already processed %s", url)
                else:
                    # extract model info from URL:
                    model_info = parse_env_canada_filename(url)
                    # download the file:
                    with tempfile.TemporaryDirectory() as temporary_path:
                        downloaded = download(
                            url,
                            temporary_path,
                            "REDIS_CACHE_ENV_CANADA",
                            model_info.model_enum.value,
                            "REDIS_ENV_CANADA_CACHE_EXPIRY",
                            fetcher,
                        )
                        if downloaded:
                            self.files_downloaded += 1
                            # If we've downloaded the file ok, we can now process it.
                            try:
                                self.grib_processor.process_grib_file(
                                    downloaded, model_info, self.session
                                )
                                # Flag the file as processed
                                flag_file_as_processed(url, self.session)
                                self.files_processed += 1
                            finally:
                                # delete the file when done.
                                os.remove(downloaded)
            except (requests.ConnectionError, requests.Timeout) as exc:
                self.connection_error_count += 1
                logger.warning("Connection error for %s: %s", url, exc)
            except Exception:
                self.exception_count += 1
                # We catch and log exceptions, but keep trying to download.
                # We intentionally catch a broad exception, as we want to try and download as much
                # as we can.
                logger.exception("unexpected exception processing %s", url)

    def process_model_run(self, model_run_hour):
        """Process a particular model run"""
        logger.info("Processing {} model run {:02d}".format(self.model_type, model_run_hour))

        # Get the urls for the current model run.
        urls = get_model_run_urls(self.now, self.model_type, model_run_hour)

        fetcher = ECCCUrlFetcher(self.now, model_run_hour)

        # Process all the urls.
        self.process_model_run_urls(urls, fetcher)

        fetcher.log_connection_summary()

        # Having completed processing, check if we're all done.
        if check_if_model_run_complete(self.session, urls):
            logger.info(
                "{} model run {:02d}:00 completed with SUCCESS".format(
                    self.model_type, model_run_hour
                )
            )

            mark_prediction_model_run_processed(
                self.session, self.model_type, self.projection, self.now, model_run_hour
            )

    def process(self):
        """Entry point for downloading and processing weather model grib files"""
        for hour in get_env_canada_model_run_hours(self.model_type):
            try:
                self.process_model_run(hour)
            except Exception:
                # We catch and log exceptions, but keep trying to process.
                # We intentionally catch a broad exception, as we want to try to process as much as we can.
                self.exception_count += 1
                logger.exception(
                    "unexpected exception processing %s model run %d",
                    self.model_type,
                    hour,
                )


def process_models():
    """downloading and processing models"""

    # set the model type requested based on arg passed via command line
    model_type = ModelEnum(sys.argv[1])
    logger.info("model type %s", model_type)

    # grab the start time.
    start_time = datetime.datetime.now()

    with wps_shared.db.database.get_write_session_scope() as session:
        env_canada = EnvCanada(session, model_type)
        env_canada.process()

        # interpolate and machine learn everything that needs interpolating.
        model_value_processor = ModelValueProcessor(session)
        model_value_processor.process(model_type)

    # calculate the execution time.
    execution_time = datetime.datetime.now() - start_time
    hours, remainder = divmod(execution_time.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    # log some info.
    logger.info(
        "%d downloaded, %d processed in total, time taken %d hours, %d minutes, %d seconds (%s)",
        env_canada.files_downloaded,
        env_canada.files_processed,
        hours,
        minutes,
        seconds,
        execution_time,
    )
    if env_canada.connection_error_count > 0:
        logger.warning("%d connection error(s) during run (hourly retries will catch missed files)", env_canada.connection_error_count)
    if env_canada.files_processed == 0 and env_canada.connection_error_count > 0:
        raise NoFilesProcessed(f"no files processed for {sys.argv[1]} — possible outage on HPFX and DD")
    if env_canada.exception_count > 0:
        raise CompletedWithSomeExceptions()
    return env_canada.files_processed


def main():
    """main script - process and download models, then do exception handling"""
    try:
        process_models()
        apply_data_retention_policy()
    except NoFilesProcessed as exc:
        # An outage on both HPFX and DD isn't something we can act on, and the hourly
        # retries pick up whatever we missed. Notify at warning severity and exit
        # cleanly so it doesn't surface as a failed job.
        logger.warning("%s", exc)
        rc_message = f":warning: No files processed for {sys.argv[1]} model data from Env Canada — hourly retries will attempt recovery"
        send_chatops_notification(rc_message, exc, severity="warning")
        sys.exit(os.EX_OK)
    except CompletedWithSomeExceptions:
        logger.warning("completed processing with some exceptions")
        sys.exit(os.EX_SOFTWARE)
    except Exception as exception:
        # We catch and log any exceptions we may have missed.
        logger.exception("unexpected exception processing")
        rc_message = f":poop: Encountered error retrieving {sys.argv[1]} model data from Env Canada"
        send_chatops_notification(rc_message, exception)
        # Exit with a failure code.
        sys.exit(os.EX_SOFTWARE)
    # We assume success if we get to this point.
    sys.exit(os.EX_OK)


if __name__ == "__main__":
    main()
