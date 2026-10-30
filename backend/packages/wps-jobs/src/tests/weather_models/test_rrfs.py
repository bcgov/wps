"""Unit tests for weather_model_jobs/rrfs.py"""

import sys
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
import requests
from weather_model_jobs import rrfs
from weather_model_jobs.common_model_fetchers import ModelValueProcessor
from weather_model_jobs.utils.process_grib import (
    RRFS_RASTER_BANDS,
    GribFileProcessor,
    ModelRunInfo,
)
from wps_shared.db.models.weather_models import ModelRunPrediction
from wps_shared.weather_models import ModelEnum, ProjectionEnum

NA_13KM = rrfs.RRFS_GRIDS["na_13km"]


class MockResponse:
    """Mocked out requests.Response object"""

    def __init__(self, status_code, content=b"", text=""):
        self.status_code = status_code
        self.content = content
        self.text = text

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(response=self)

BASE_URL = "https://nomads.ncep.noaa.gov/pub/data/nccf/com/rrfs/prod"

# Excerpts of real .idx files (rrfs.t12z.2dfld.13km.f044.na and f048.na from 2026-10-29), with the
# records on either side of the ones we download.
IDX_F044 = """73:26984941:d=2026102912:POROS:surface:44 hour fcst:
74:27163115:d=2026102912:TMP:2 m above ground:44 hour fcst:
75:27918918:d=2026102912:SPFH:2 m above ground:44 hour fcst:
77:29455528:d=2026102912:DEPR:2 m above ground:44 hour fcst:
78:30050035:d=2026102912:RH:2 m above ground:44 hour fcst:
79:30788192:d=2026102912:TMAX:2 m above ground:43-44 hour max fcst:
87:34176922:d=2026102912:MASSDEN:8 m above ground:44 hour fcst:aerosol=Dust dry:aerosol_size >=2.5e-06,<1e-05
88:34278053:d=2026102912:UGRD:10 m above ground:44 hour fcst:
89:35165283:d=2026102912:VGRD:10 m above ground:44 hour fcst:
90:36024654:d=2026102912:MAXUW:10 m above ground:43-44 hour max fcst:
96:38645777:d=2026102912:PRATE:surface:43-44 hour max fcst:
97:39180468:d=2026102912:APCP:surface:43-44 hour acc fcst:
98:39465140:d=2026102912:APCP:surface:0-44 hour acc fcst:
99:40098095:d=2026102912:TSNOWP:surface:0-44 hour acc fcst:
"""

IDX_F048_APCP = """97:39421353:d=2026102912:APCP:surface:47-48 hour acc fcst:
98:39708565:d=2026102912:APCP:surface:0-2 day acc fcst:
99:40356573:d=2026102912:TSNOWP:surface:0-2 day acc fcst:
"""

IDX_F000 = """58:20240926:d=2026102912:TMP:2 m above ground:anl:
59:20500000:d=2026102912:SPFH:2 m above ground:anl:
62:23086652:d=2026102912:RH:2 m above ground:anl:
63:23500000:d=2026102912:DPT:2 m above ground:anl:
66:24683720:d=2026102912:UGRD:10 m above ground:anl:
67:25555537:d=2026102912:VGRD:10 m above ground:anl:
"""


@pytest.mark.parametrize(
    "model_cycle,expected_hours",
    [
        ("00", [20, 44, 68]),
        ("06", [14, 38, 62]),
        ("12", [8, 32, 56, 80]),
        ("18", [2, 26, 50, 74]),
    ],
)
def test_forecast_hours_are_valid_at_20_utc(model_cycle, expected_hours):
    hours = rrfs.get_rrfs_forecast_hours(model_cycle)
    assert hours == expected_hours
    assert all((int(model_cycle) + hour) % 24 == 20 for hour in hours)


def test_get_rrfs_model_run_download_urls_for_00_utc():
    urls = list(
        rrfs.get_rrfs_model_run_download_urls(
            datetime(2026, 11, 3, 0, tzinfo=timezone.utc), "00", NA_13KM, BASE_URL
        )
    )
    assert urls == [
        f"{BASE_URL}/rrfs.20261103/00/rrfs.t00z.2dfld.13km.f020.na.grib2",
        f"{BASE_URL}/rrfs.20261103/00/rrfs.t00z.2dfld.13km.f044.na.grib2",
        f"{BASE_URL}/rrfs.20261103/00/rrfs.t00z.2dfld.13km.f068.na.grib2",
    ]


def test_get_rrfs_model_run_download_urls_for_alaska_grid():
    urls = list(
        rrfs.get_rrfs_model_run_download_urls(
            datetime(2026, 11, 3, 18, tzinfo=timezone.utc), "18", rrfs.RRFS_GRIDS["ak_3km"], BASE_URL
        )
    )
    assert urls[0] == f"{BASE_URL}/rrfs.20261103/18/rrfs.t18z.2dfld.3km.f002.ak.grib2"


def test_parse_rrfs_url_for_timestamps_crosses_days():
    url = f"{BASE_URL}/rrfs.20261103/18/rrfs.t18z.2dfld.13km.f074.na.grib2"
    model_run_timestamp, prediction_timestamp = rrfs.parse_rrfs_url_for_timestamps(url)
    assert model_run_timestamp == datetime(2026, 11, 3, 18, tzinfo=timezone.utc)
    assert prediction_timestamp == datetime(2026, 11, 6, 20, tzinfo=timezone.utc)


def test_parse_rrfs_url_for_timestamps_rejects_other_urls():
    with pytest.raises(ValueError):
        rrfs.parse_rrfs_url_for_timestamps(f"{BASE_URL}/rrfs.20261103/18/rrfs.t18z.natlev.f074.grib2")


def test_records_are_in_band_order():
    """The download writes records in RRFS_RECORDS order; the grib processor reads bands by number."""
    assert [name for name, _, _ in rrfs.RRFS_RECORDS] == list(RRFS_RASTER_BANDS)
    assert list(RRFS_RASTER_BANDS.values()) == list(range(1, len(RRFS_RASTER_BANDS) + 1))


def test_byte_ranges_take_the_run_total_precip_not_the_last_hour():
    ranges = rrfs.get_record_byte_ranges(IDX_F044, 44)
    assert ranges == [
        (27163115, 27918917),  # TMP 2 m
        (30050035, 30788191),  # RH 2 m
        (34278053, 35165282),  # UGRD 10 m
        (35165283, 36024653),  # VGRD 10 m
        (39465140, 40098094),  # APCP 0-44 hour acc, not 43-44
    ]


def test_byte_ranges_read_run_totals_labelled_in_days():
    """wgrib2 labels whole-day accumulations in days: hour 48 is '0-2 day acc'."""
    idx = IDX_F044.replace("44 hour fcst", "48 hour fcst").split("96:")[0] + IDX_F048_APCP
    assert rrfs.get_record_byte_ranges(idx, 48)[-1] == (39708565, 40356572)


def test_byte_ranges_skip_precip_at_hour_zero():
    ranges = rrfs.get_record_byte_ranges(IDX_F000, 0)
    assert ranges == [
        (20240926, 20499999),
        (23086652, 23499999),
        (24683720, 25555536),
        (25555537, None),  # last record in the file: read to the end
    ]


def test_byte_ranges_refuse_a_run_total_for_another_hour():
    with pytest.raises(ValueError, match="APCP:surface"):
        rrfs.get_record_byte_ranges(IDX_F044, 45)


def test_byte_ranges_refuse_a_missing_record():
    idx = IDX_F044.replace(":RH:", ":XX:")
    with pytest.raises(ValueError, match="RH:2 m above ground"):
        rrfs.get_record_byte_ranges(idx, 44)


def test_download_rrfs_records_writes_only_the_requested_ranges(monkeypatch, tmp_path):
    url = f"{BASE_URL}/rrfs.20261029/12/rrfs.t12z.2dfld.13km.f044.na.grib2"
    requested = []

    def get(request_url, headers=None, timeout=None):
        if request_url == f"{url}.idx":
            return MockResponse(status_code=200, text=IDX_F044)
        requested.append(headers["Range"])
        return MockResponse(status_code=206, content=headers["Range"].encode() + b";")

    monkeypatch.setattr(requests, "get", get)

    target = rrfs.download_rrfs_records(url, str(tmp_path), 44)

    assert requested == [
        "bytes=27163115-27918917",
        "bytes=30050035-30788191",
        "bytes=34278053-35165282",
        "bytes=35165283-36024653",
        "bytes=39465140-40098094",
    ]
    with open(target, "rb") as file:
        assert file.read() == ";".join(requested).encode() + b";"


def test_download_rrfs_records_returns_none_before_the_file_is_published(monkeypatch, tmp_path):
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: MockResponse(status_code=404))
    url = f"{BASE_URL}/rrfs.20261029/12/rrfs.t12z.2dfld.13km.f044.na.grib2"
    assert rrfs.download_rrfs_records(url, str(tmp_path), 44) is None


def test_download_rrfs_records_refuses_a_whole_file_response(monkeypatch, tmp_path):
    """A server that ignores Range sends the whole 150 MB file; that must not pass as one record."""
    url = f"{BASE_URL}/rrfs.20261029/12/rrfs.t12z.2dfld.13km.f044.na.grib2"

    def get(request_url, headers=None, timeout=None):
        if request_url.endswith(".idx"):
            return MockResponse(status_code=200, text=IDX_F044)
        return MockResponse(status_code=200, content=b"whole file")

    monkeypatch.setattr(requests, "get", get)
    with pytest.raises(ValueError, match="partial response"):
        rrfs.download_rrfs_records(url, str(tmp_path), 44)


def _make_rrfs(monkeypatch, grid=None):
    monkeypatch.setattr("weather_model_jobs.noaa.GribFileProcessor", MagicMock)
    settings = {"RRFS_GRID": grid} if grid else {}
    monkeypatch.setattr(rrfs.config, "get", lambda key, default=None: settings.get(key, default))
    return rrfs.RRFS(MagicMock())


def test_grid_defaults_to_north_america_13km(monkeypatch):
    job = _make_rrfs(monkeypatch)
    assert job.grid == NA_13KM
    assert job.projection == ProjectionEnum.RRFS_NA_13KM
    assert job.base_url == rrfs.DEFAULT_RRFS_BASE_URL


def test_grid_setting_selects_alaska_3km(monkeypatch):
    job = _make_rrfs(monkeypatch, grid="ak_3km")
    assert job.projection == ProjectionEnum.RRFS_AK_3KM


def test_unknown_grid_setting_is_refused(monkeypatch):
    with pytest.raises(ValueError, match="conus_3km"):
        _make_rrfs(monkeypatch, grid="conus_3km")


def test_process_model_run_reads_yesterdays_run_before_its_hour(monkeypatch):
    """At 03:00 UTC the latest 18Z run is yesterday's, for both the URLs and the completion mark."""
    job = _make_rrfs(monkeypatch)
    job.now = datetime(2026, 11, 4, 3, 15, tzinfo=timezone.utc)
    processed = []
    monkeypatch.setattr(job, "process_model_run_urls", processed.extend)
    monkeypatch.setattr(rrfs, "check_if_model_run_complete", lambda *_: True)
    mark = MagicMock()
    monkeypatch.setattr(rrfs, "mark_prediction_model_run_processed", mark)

    job.process_model_run("18")

    assert processed[0] == f"{rrfs.DEFAULT_RRFS_BASE_URL}/rrfs.20261103/18/rrfs.t18z.2dfld.13km.f002.na.grib2"
    mark.assert_called_once_with(job.session, ModelEnum.RRFS, ProjectionEnum.RRFS_NA_13KM, job.now, "18")


def test_process_model_run_does_not_mark_an_incomplete_run(monkeypatch):
    job = _make_rrfs(monkeypatch)
    monkeypatch.setattr(job, "process_model_run_urls", lambda urls: None)
    monkeypatch.setattr(rrfs, "check_if_model_run_complete", lambda *_: False)
    mark = MagicMock()
    monkeypatch.setattr(rrfs, "mark_prediction_model_run_processed", mark)

    job.process_model_run("00")

    mark.assert_not_called()


def test_process_url_processes_the_subset_with_rrfs_model_info(monkeypatch, tmp_path):
    job = _make_rrfs(monkeypatch)
    url = f"{BASE_URL}/rrfs.20261103/00/rrfs.t00z.2dfld.13km.f044.na.grib2"
    monkeypatch.setattr(rrfs, "get_processed_file_record", lambda *_: None)
    flagged = []
    monkeypatch.setattr(rrfs, "flag_file_as_processed", lambda u, s: flagged.append(u))
    downloads = []

    def download(download_url, path, forecast_hour):
        downloads.append((download_url, forecast_hour))
        return str(tmp_path / "subset.grib2")

    monkeypatch.setattr(rrfs, "download_rrfs_records", download)

    job.process_url(url)

    assert downloads == [(url, 44)]
    model_info = job.grib_processor.process_grib_file.call_args.args[1]
    assert model_info.model_enum == ModelEnum.RRFS
    assert model_info.projection == ProjectionEnum.RRFS_NA_13KM
    assert model_info.prediction_timestamp == datetime(2026, 11, 4, 20, tzinfo=timezone.utc)
    assert flagged == [url]
    assert (job.files_downloaded, job.files_processed) == (1, 1)


def test_process_url_skips_files_already_processed(monkeypatch):
    job = _make_rrfs(monkeypatch)
    monkeypatch.setattr(rrfs, "get_processed_file_record", lambda *_: object())
    download = MagicMock()
    monkeypatch.setattr(rrfs, "download_rrfs_records", download)

    job.process_url(f"{BASE_URL}/rrfs.20261103/00/rrfs.t00z.2dfld.13km.f044.na.grib2")

    download.assert_not_called()


def test_get_raster_bands_reads_the_rrfs_layout():
    dataset = MagicMock()
    dataset.GetRasterBand.side_effect = lambda number: f"band {number}"
    processor = GribFileProcessor.__new__(GribFileProcessor)
    run = datetime(2026, 11, 3, 0, tzinfo=timezone.utc)

    bands = processor.get_raster_bands(
        dataset, ModelRunInfo(ModelEnum.RRFS, ProjectionEnum.RRFS_NA_13KM, run, run.replace(hour=20))
    )
    assert bands == ("band 1", "band 2", "band 3", "band 4", "band 5")

    bands = processor.get_raster_bands(
        dataset, ModelRunInfo(ModelEnum.RRFS, ProjectionEnum.RRFS_NA_13KM, run, run)
    )
    assert bands == ("band 1", "band 2", "band 3", "band 4", None)


@pytest.mark.parametrize(
    "forecast_hours",
    [
        [20, 44, 68],  # the hours the job downloads from a 00Z run
        [12, 36, 60],  # 12:00 UTC is a NAM accumulation hour, where bucket logic would change the totals
    ],
)
def test_run_total_precip_becomes_per_interval_and_24_hour_precip(monkeypatch, forecast_hours):
    """RRFS stores the run-total APCP, so per-interval precip is the difference between predictions
    of the same run, as for GFS. NAM's bucket accumulation must not be applied to it."""
    run_start = datetime(2026, 11, 3, 0, tzinfo=timezone.utc)
    run_totals = dict(zip(forecast_hours, [1.0, 3.5, 3.5]))
    predictions = [
        ModelRunPrediction(
            prediction_timestamp=run_start.replace(day=3 + hour // 24, hour=hour % 24),
            apcp_sfc_0=total,
            tmp_tgl_2=5.0,
            rh_tgl_2=80.0,
        )
        for hour, total in run_totals.items()
    ]
    stored = {}

    class Query:
        """Answers _calculate_delta_precip's query with the latest prediction stored so far."""

        def __getattr__(self, name):
            return lambda *args, **kwargs: self

        def first(self):
            return stored[max(stored)] if stored else None

    session = MagicMock()
    session.query.side_effect = lambda *args: Query()
    session.add.side_effect = lambda prediction: stored.__setitem__(
        prediction.prediction_timestamp, prediction
    )
    module = "weather_model_jobs.common_model_fetchers"
    monkeypatch.setattr(f"{module}.get_stations_synchronously", lambda: [])
    monkeypatch.setattr(f"{module}.StationMachineLearning", MagicMock())
    monkeypatch.setattr(f"{module}.get_model_run_predictions_for_station", lambda *_: predictions)
    monkeypatch.setattr(
        f"{module}.get_weather_station_model_prediction",
        lambda session, code, run_id, timestamp: stored.get(timestamp),
    )
    # Observed precipitation fills the part of the first 24 hours before the run started.
    monkeypatch.setattr(f"{module}.get_accumulated_precipitation", lambda *_: 0.4)

    processor = ModelValueProcessor(session)
    model_run = MagicMock(id=1, prediction_run_timestamp=run_start)
    station = MagicMock(code=322, lat=50.0, long=-120.0)
    processor._process_model_run_for_station(model_run, station, ModelEnum.RRFS)

    results = [stored[prediction.prediction_timestamp] for prediction in predictions]
    assert [result.apcp_sfc_0 for result in results] == [1.0, 3.5, 3.5]
    assert [result.delta_precip for result in results] == pytest.approx([1.0, 2.5, 0.0])
    assert [result.precip_24h for result in results] == pytest.approx([1.4, 2.5, 0.0])


def test_process_models_delegates_the_verdict_to_judge_run(monkeypatch):
    monkeypatch.setattr("wps_shared.db.database.get_write_session_scope", MagicMock())
    value_processor = MagicMock()
    monkeypatch.setattr(rrfs, "ModelValueProcessor", value_processor)
    monkeypatch.setattr("weather_model_jobs.noaa.GribFileProcessor", MagicMock)

    def finished_run(self):
        self.files_processed = 3
        self.connection_error_count = 1
        self.exception_count = 0

    monkeypatch.setattr(rrfs.RRFS, "process", finished_run)
    judge_run = MagicMock(return_value=3)
    monkeypatch.setattr(rrfs, "judge_run", judge_run)

    assert rrfs.process_models() == 3

    job = judge_run.call_args.args[0]
    assert (job.files_processed, job.connection_error_count, job.exception_count) == (3, 1, 0)
    assert judge_run.call_args.kwargs == {"source": "NOAA", "model": "RRFS"}
    value_processor.return_value.process.assert_called_once_with(ModelEnum.RRFS)


def test_main_delegates_to_the_shared_runner(monkeypatch):
    run_model_job = MagicMock()
    monkeypatch.setattr(rrfs, "run_model_job", run_model_job)
    monkeypatch.setattr(sys, "argv", ["argv"])

    rrfs.main()

    run_model_job.assert_called_once_with(rrfs.process_models, source="NOAA", model="RRFS")
