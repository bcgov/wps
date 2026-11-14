"""A script that downloads RRFS (Rapid Refresh Forecast System) model runs from NOAA.

NOMADS has no grib filter for RRFS, so instead of a filter URL each file is subset by reading its
.idx and downloading only the records we need with HTTP byte ranges.
"""

import datetime
import logging
import os
import re
import tempfile
from dataclasses import dataclass
from typing import Generator, List, Optional, Tuple

import requests
import wps_shared.db.database
from sqlalchemy.orm import Session
from weather_model_jobs.common_model_fetchers import (
    ModelValueProcessor,
    check_if_model_run_complete,
    flag_file_as_processed,
)
from weather_model_jobs.model_job_runner import judge_run, run_model_job
from weather_model_jobs.noaa import (
    NOAA,
    adjust_model_day,
    get_year_mo_date_string_from_datetime,
    mark_prediction_model_run_processed,
)
from weather_model_jobs.utils.process_grib import ModelRunInfo
from wps_shared import config
from wps_shared.db.crud.weather_models import get_processed_file_record
from wps_shared.weather_models import ModelEnum, ProjectionEnum
from wps_shared.wps_logging import configure_logging

# If running as its own process, configure logging appropriately.
if __name__ == "__main__":
    configure_logging()

logger = logging.getLogger(__name__)

SOURCE = "NOAA"
MODEL = ModelEnum.RRFS.value

# The AWS bucket (https://noaa-rrfs-ops-pds.s3.amazonaws.com) uses the same layout.
DEFAULT_RRFS_BASE_URL = "https://nomads.ncep.noaa.gov/pub/data/nccf/com/rrfs/prod"


@dataclass(frozen=True)
class RRFSGrid:
    """An RRFS output grid, named the way it appears in RRFS file names."""

    resolution: str
    domain: str
    projection: ProjectionEnum


RRFS_GRIDS = {
    # Covers all of the subregion we store (48-60N, 139-114W). Close to the 12 km NAM grid.
    "na_13km": RRFSGrid("13km", "na", ProjectionEnum.RRFS_NA_13KM),
    # Covers about 94% of the subregion. The 3 km CONUS grid stops near 50N, so it isn't offered.
    "ak_3km": RRFSGrid("3km", "ak", ProjectionEnum.RRFS_AK_3KM),
}
DEFAULT_RRFS_GRID = "na_13km"

# RRFS runs every hour, but only the 00, 06, 12 and 18 UTC runs go out to 84 hours.
RRFS_MODEL_RUN_HOURS = ("00", "06", "12", "18")
RRFS_MAX_FORECAST_HOUR = 84
# RRFS has hourly output, so we take the 20:00 UTC (12:00 PST) prediction directly instead of
# interpolating it from 18:00 and 21:00 as we do for GFS.
NOON_UTC_HOUR = 20

# The records we download, in band order (see RRFS_RASTER_BANDS). The files carry two APCP records
# from hour 2 on: the last hour, and the total since the start of the run. We keep the run total,
# like GFS, so delta and 24 hour precip are differences between predictions of the same run.
RRFS_RECORDS = (
    ("tmp_tgl_2", "TMP", "2 m above ground"),
    ("rh_tgl_2", "RH", "2 m above ground"),
    ("u_comp_wind_10m", "UGRD", "10 m above ground"),
    ("v_comp_wind_10m", "VGRD", "10 m above ground"),
    ("cumulative_apcp_sfc_0", "APCP", "surface"),
)
INSTANTANEOUS_FORECAST = re.compile(r"^(anl|\d+ (hour|day) fcst)$")
RUN_TOTAL_ACCUMULATION = re.compile(r"^0-(\d+) (hour|day) acc fcst$")
URL_PATTERN = re.compile(r"/rrfs\.(\d{8})/(\d{2})/rrfs\.t\d{2}z\.2dfld\.[^/]+\.f(\d{3})\.[a-z]+\.grib2$")


def get_rrfs_grid() -> RRFSGrid:
    """Return the grid named by the RRFS_GRID setting."""
    name = config.get("RRFS_GRID", DEFAULT_RRFS_GRID)
    if name not in RRFS_GRIDS:
        raise ValueError(f"Unknown RRFS_GRID {name!r}, expected one of {sorted(RRFS_GRIDS)}")
    return RRFS_GRIDS[name]


def get_rrfs_forecast_hours(model_cycle: str) -> List[int]:
    """Forecast hours of a model run that are valid at 20:00 UTC."""
    first_hour = (NOON_UTC_HOUR - int(model_cycle)) % 24
    return list(range(first_hour, RRFS_MAX_FORECAST_HOUR + 1, 24))


def get_rrfs_model_run_download_urls(
    download_date: datetime.datetime, model_cycle: str, grid: RRFSGrid, base_url: str
) -> Generator[str, None, None]:
    """Yield the grib file URLs of an RRFS model run."""
    year_mo_date = get_year_mo_date_string_from_datetime(download_date)
    for fcst_hour in get_rrfs_forecast_hours(model_cycle):
        yield (
            f"{base_url}/rrfs.{year_mo_date}/{model_cycle}/"
            f"rrfs.t{model_cycle}z.2dfld.{grid.resolution}.f{fcst_hour:03d}.{grid.domain}.grib2"
        )


def parse_rrfs_url_for_timestamps(url: str) -> Tuple[datetime.datetime, datetime.datetime]:
    """Interpret the model_run_timestamp and prediction_timestamp from an RRFS grib file URL"""
    # sample URL: 'https://nomads.ncep.noaa.gov/pub/data/nccf/com/rrfs/prod/rrfs.20261103/00/rrfs.t00z.2dfld.13km.f020.na.grib2'
    match = URL_PATTERN.search(url)
    if match is None:
        raise ValueError(f"Not an RRFS grib file URL: {url}")
    model_run_date, model_run_hour, forecast_hour = match.groups()
    model_run_timestamp = datetime.datetime.strptime(
        model_run_date + model_run_hour, "%Y%m%d%H"
    ).replace(tzinfo=datetime.timezone.utc)
    prediction_timestamp = model_run_timestamp + datetime.timedelta(hours=int(forecast_hour))
    return (model_run_timestamp, prediction_timestamp)


def _accumulation_hours(forecast: str) -> Optional[int]:
    """Hours in a run-total accumulation label, e.g. '0-44 hour acc fcst' or '0-2 day acc fcst'."""
    match = RUN_TOTAL_ACCUMULATION.match(forecast)
    if match is None:
        return None
    amount, unit = match.groups()
    return int(amount) * (24 if unit == "day" else 1)


def get_record_byte_ranges(idx: str, forecast_hour: int) -> List[Tuple[int, Optional[int]]]:
    """Return the (first, last) byte of each record in RRFS_RECORDS, read from a grib .idx file.

    The last byte is None when the record is the last one in the file. Records not needed at this
    forecast hour (precipitation at hour 0) are left out.
    """
    # idx lines look like '98:39465140:d=2026102912:APCP:surface:0-44 hour acc fcst:'
    entries = []
    for line in idx.splitlines():
        fields = line.split(":")
        if len(fields) >= 6:
            entries.append((int(fields[1]), fields[3], fields[4], fields[5]))

    ranges = []
    for _, variable, level in RRFS_RECORDS:
        if variable == "APCP" and forecast_hour == 0:
            continue
        matches = []
        for index, (offset, entry_variable, entry_level, forecast) in enumerate(entries):
            if (entry_variable, entry_level) != (variable, level):
                continue
            if variable == "APCP":
                found = _accumulation_hours(forecast) == forecast_hour
            else:
                found = INSTANTANEOUS_FORECAST.match(forecast) is not None
            if found:
                last = entries[index + 1][0] - 1 if index + 1 < len(entries) else None
                matches.append((offset, last))
        if len(matches) != 1:
            raise ValueError(
                f"Expected one {variable}:{level} record for hour {forecast_hour}, found {len(matches)}"
            )
        ranges.append(matches[0])
    return ranges


def download_rrfs_records(url: str, path: str, forecast_hour: int) -> Optional[str]:
    """Download the records we need from an RRFS grib file into one grib file under path.

    Returns None when the file isn't published yet.
    """
    response = requests.get(f"{url}.idx", timeout=60)
    if response.status_code == 404:
        logger.info("404 error for %s.idx", url)
        return None
    response.raise_for_status()
    byte_ranges = get_record_byte_ranges(response.text, forecast_hour)

    target = os.path.join(path, os.path.basename(url))
    with open(target, "wb") as file_object:
        for first, last in byte_ranges:
            byte_range = f"bytes={first}-{'' if last is None else last}"
            response = requests.get(url, headers={"Range": byte_range}, timeout=60)
            response.raise_for_status()
            if response.status_code != 206:
                raise ValueError(f"Expected a partial response for {byte_range} of {url}, got {response.status_code}")
            file_object.write(response.content)
    return target


class RRFS(NOAA):
    """Downloads and processes RRFS model runs, reusing the NOAA job's error handling."""

    def __init__(self, session: Session):
        super().__init__(session, ModelEnum.RRFS)
        self.grid = get_rrfs_grid()
        self.projection = self.grid.projection
        self.base_url = config.get("RRFS_BASE_URL", DEFAULT_RRFS_BASE_URL)

    def process_url(self, url):
        """Download and process a single grib file URL, skipping if already processed."""
        if get_processed_file_record(self.session, url):
            logger.debug("file already processed %s", url)
            return

        model_run_timestamp, prediction_timestamp = parse_rrfs_url_for_timestamps(url)
        forecast_hour = int((prediction_timestamp - model_run_timestamp).total_seconds() // 3600)
        model_info = ModelRunInfo(
            self.model_type, self.projection, model_run_timestamp, prediction_timestamp
        )

        with tempfile.TemporaryDirectory() as temporary_path:
            downloaded = download_rrfs_records(url, temporary_path, forecast_hour)
            if downloaded:
                self.files_downloaded += 1
                self.grib_processor.process_grib_file(downloaded, model_info, self.session)
                flag_file_as_processed(url, self.session)
                self.files_processed += 1

    def process_model_run(self, model_run_hour):
        """Process a particular model run"""
        logger.info("Processing %s model run %s", self.model_type, model_run_hour)
        model_run_date = adjust_model_day(self.now, model_run_hour)
        urls = list(
            get_rrfs_model_run_download_urls(model_run_date, model_run_hour, self.grid, self.base_url)
        )

        self.process_model_run_urls(urls)

        if check_if_model_run_complete(self.session, urls):
            logger.info("%s model run %s:00 completed with SUCCESS", self.model_type, model_run_hour)
            mark_prediction_model_run_processed(
                self.session, self.model_type, self.projection, self.now, model_run_hour
            )

    def process(self):
        """Entry point for downloading and processing RRFS grib files"""
        for hour in RRFS_MODEL_RUN_HOURS:
            try:
                self.process_model_run(hour)
            except Exception:
                # We catch and log exceptions, but keep trying to process.
                self.exception_count += 1
                logger.exception("unexpected exception processing RRFS model run %s", hour)


def process_models():
    """Download and process RRFS model runs"""
    start_time = datetime.datetime.now()

    with wps_shared.db.database.get_write_session_scope() as session:
        rrfs = RRFS(session)
        rrfs.process()

        # interpolate and machine learn everything that needs interpolating.
        model_value_processor = ModelValueProcessor(session)
        model_value_processor.process(ModelEnum.RRFS)

    execution_time = datetime.datetime.now() - start_time
    logger.info(
        "%d downloaded, %d processed in total, time taken %s",
        rrfs.files_downloaded,
        rrfs.files_processed,
        execution_time,
    )
    return judge_run(rrfs, source=SOURCE, model=MODEL)


def main():
    """main script - process and download models, then do exception handling"""
    run_model_job(process_models, source=SOURCE, model=MODEL)


if __name__ == "__main__":
    main()
