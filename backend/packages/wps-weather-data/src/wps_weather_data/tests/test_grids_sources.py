import io
import urllib.error
import urllib.request
from datetime import UTC, datetime

import pytest

from wps_weather_data.grids import sources
from wps_weather_data.grids.models import MODELS
from wps_weather_data.grids.sources import (
    EcmwfOpenData,
    MscDatamart,
    NoaaGfs,
    NotPublishedError,
    download,
)

RUN = datetime(2026, 11, 23, 12, tzinfo=UTC)

GFS_INDEX = """\
1:0:d=2026112312:PRMSL:mean sea level:9 hour fcst:
2:100:d=2026112312:TMP:2 m above ground:9 hour fcst:
3:250:d=2026112312:TMP:surface:9 hour fcst:
4:300:d=2026112312:APCP:surface:6-9 hour acc fcst:
5:340:d=2026112312:APCP:surface:0-9 hour acc fcst:
"""
ECMWF_INDEX = """\
{"type": "fc", "step": "24", "levelist": "2", "levtype": "sol", "param": "sot", "_offset": 0, "_length": 10}
{"type": "fc", "step": "24", "levtype": "sfc", "param": "2t", "_offset": 10, "_length": 20}
"""


class Response(io.BytesIO):
    """What urlopen returns."""

    def __init__(self, content: bytes, status: int = 200, length: int | None = None):
        super().__init__(content)
        self.status = status
        self.headers = {"Content-Length": str(len(content) if length is None else length)}


def http_error(code: int) -> urllib.error.HTTPError:
    return urllib.error.HTTPError("https://source/file", code, "error", {}, None)


@pytest.fixture
def answers(monkeypatch):
    """Answers to give urlopen in turn: responses, or errors to raise. Returns the list to fill,
    and the requests made."""
    queued, requests = [], []

    def urlopen(request, timeout):
        requests.append(request)
        answer = queued.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer

    monkeypatch.setattr(urllib.request, "urlopen", urlopen)
    monkeypatch.setattr(sources.time, "sleep", lambda seconds: None)
    sources.read_text.cache_clear()
    yield queued, requests
    sources.read_text.cache_clear()


def test_download_writes_the_file(answers, tmp_path):
    answers[0].append(Response(b"grib"))

    download("https://source/file", tmp_path / "a")

    assert (tmp_path / "a").read_bytes() == b"grib"
    assert answers[1][0].get_header("Range") is None


@pytest.mark.parametrize(
    "failure",
    [
        Response(b"gr", length=4),
        http_error(503),
        urllib.error.URLError("refused"),
        TimeoutError("timed out"),
    ],
    ids=["ends early", "busy", "cannot connect", "times out"],
)
def test_download_is_retried(answers, tmp_path, failure):
    answers[0].extend([failure, Response(b"grib")])

    download("https://source/file", tmp_path / "a")

    assert (tmp_path / "a").read_bytes() == b"grib"


def test_download_gives_up_after_its_attempts(answers, tmp_path):
    answers[0].extend([http_error(503) for _ in range(sources.ATTEMPTS)])

    with pytest.raises(urllib.error.HTTPError):
        download("https://source/file", tmp_path / "a")
    assert len(answers[1]) == sources.ATTEMPTS


def test_a_missing_file_is_not_published_and_not_retried(answers, tmp_path):
    answers[0].append(http_error(404))

    with pytest.raises(NotPublishedError):
        download("https://source/file", tmp_path / "a")
    assert len(answers[1]) == 1


def test_other_http_errors_are_not_retried(answers, tmp_path):
    answers[0].append(http_error(403))

    with pytest.raises(urllib.error.HTTPError):
        download("https://source/file", tmp_path / "a")
    assert len(answers[1]) == 1


@pytest.mark.parametrize("end, header", [(19, "bytes=10-19"), (None, "bytes=10-")])
def test_download_can_ask_for_a_range_of_bytes(answers, tmp_path, end, header):
    answers[0].append(Response(b"0123456789", status=206))

    download("https://source/file", tmp_path / "a", (10, end))

    assert answers[1][0].get_header("Range") == header


def test_a_whole_file_in_answer_to_a_range_is_refused(answers, tmp_path):
    answers[0].append(Response(b"the whole file", status=200))

    with pytest.raises(ValueError, match="byte range"):
        download("https://source/file", tmp_path / "a", (0, 3))


def test_msc_has_a_file_per_field():
    source = MscDatamart("HRDPS", "model_hrdps/continental/2.5km", "RLatLon0.0225")

    assert source.url(RUN, 6, "TMP_AGL-2m") == (
        "https://dd.weather.gc.ca/today/model_hrdps/continental/2.5km/12/006/"
        "20261123T12Z_MSC_HRDPS_TMP_AGL-2m_RLatLon0.0225_PT006H.grib2"
    )


@pytest.mark.parametrize(
    "layer, expected",
    [
        ("PRMSL:mean sea level:", (0, 99)),
        ("TMP:2 m above ground:", (100, 249)),
        # Not the last three hours' total, and the last field has no end.
        ("APCP:surface:0-", (340, None)),
        ("RH:2 m above ground:", None),
    ],
)
def test_gfs_fields_are_found_in_the_index(layer, expected):
    assert NoaaGfs().find(GFS_INDEX, layer) == expected


def test_gfs_takes_the_last_of_two_totals_since_the_start():
    index = (
        "1:0:d=2026112312:APCP:surface:0-3 hour acc fcst:\n"
        "2:50:d=2026112312:APCP:surface:0-3 hour acc fcst:\n"
        "3:90:d=2026112312:CAPE:surface:3 hour fcst:\n"
    )
    assert NoaaGfs().find(index, "APCP:surface:0-") == (50, 89)


@pytest.mark.parametrize("layer, expected", [("2t", (10, 29)), ("sot", None), ("2d", None)])
def test_ecmwf_surface_fields_are_found_in_the_index(layer, expected):
    assert EcmwfOpenData().find(ECMWF_INDEX, layer) == expected


def test_an_indexed_field_is_fetched_by_its_bytes(answers, tmp_path):
    answers[0].extend([Response(GFS_INDEX.encode()), Response(b"x" * 150, status=206)])

    NoaaGfs().fetch(RUN, 9, "TMP:2 m above ground:", tmp_path / "a")

    index, grib = answers[1]
    url = "https://noaa-gfs-bdp-pds.s3.amazonaws.com/gfs.20261123/12/atmos/gfs.t12z.pgrb2.0p25.f009"
    assert index == f"{url}.idx"
    assert (grib.full_url, grib.get_header("Range")) == (url, "bytes=100-249")


def test_ecmwf_urls():
    url = (
        "https://storage.googleapis.com/ecmwf-open-data/20261123/12z/ifs/0p1/oper/"
        "20261123120000-24h-oper-fc-sfc"
    )
    assert EcmwfOpenData().urls(RUN, 24) == (f"{url}.grib2", f"{url}.index")


def test_an_hours_index_is_read_once(answers):
    answers[0].append(Response(GFS_INDEX.encode()))
    gfs = NoaaGfs()

    assert gfs.exists(RUN, 9, "TMP:2 m above ground:")
    assert not gfs.exists(RUN, 9, "RH:2 m above ground:")
    assert len(answers[1]) == 1


def test_a_missing_index_is_not_published_and_is_asked_for_again(answers):
    answers[0].extend([http_error(404), Response(GFS_INDEX.encode())])
    gfs = NoaaGfs()

    assert not gfs.exists(RUN, 9, "TMP:2 m above ground:")
    assert gfs.exists(RUN, 9, "TMP:2 m above ground:")


@pytest.mark.parametrize("run_hour, last", [(0, 240), (6, 144), (12, 240), (18, 144)])
def test_ecmwf_runs_have_different_hours(run_hour, last):
    hours = MODELS["ECMWF"].forecast_hours(RUN.replace(hour=run_hour))

    assert hours[-1] == last
    assert 147 not in hours


def test_each_models_daily_run_is_one_it_makes_at_full_length():
    for model in MODELS.values():
        assert model.history_run_hour in model.run_hours
        assert model.history_run_hour not in model.other_hours
