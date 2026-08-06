from datetime import datetime

from shapely import wkt
from wps_shared.db.models.weather_models import ModelRunGridSubsetPrediction, ProcessedModelRunUrl
from wps_shared.schemas.stations import Season, WeatherStation


class MockResponse:
    """Mocked out request.Response object (used by the NOAA download path, which has no
    fetcher and stays on plain requests)."""

    def __init__(self, status_code, content=None):
        self.status_code = status_code
        self._content = content

    def iter_content(self, chunk_size=1):
        """Mimic requests.Response.iter_content for streaming downloads"""
        return iter((self._content,)) if self._content else iter(())

    def close(self):
        """Mimic requests.Response.close"""


class FakeFetcher:
    """Stand-in for ECCCUrlFetcher: writes canned content (or raises) instead of hitting
    the network. Used by patching env_canada.ECCCUrlFetcher with make_fake_fetcher_factory(...)."""

    def __init__(self, content: bytes = b"", ok: bool = True, raises: Exception | None = None):
        self._content = content
        self._ok = ok
        self._raises = raises

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_info):
        return False

    async def fetch(self, url, target):
        if self._raises is not None:
            raise self._raises
        if self._ok:
            with open(target, "wb") as file_object:
                file_object.write(self._content)
        return self._ok

    def log_connection_summary(self):
        pass


def make_fake_fetcher_factory(
    content: bytes = b"", ok: bool = True, raises: Exception | None = None
):
    """Return a callable usable as a drop-in replacement for ECCCUrlFetcher's constructor."""

    def factory(*args, **kwargs):
        return FakeFetcher(content, ok, raises)

    return factory


def mock_get_model_run_predictions(*args):
    result = [
        ModelRunGridSubsetPrediction(
            tmp_tgl_2=[2, 3, 4, 5],
            rh_tgl_2=[10, 20, 30, 40],
            apcp_sfc_0=[2, 4, 3, 6],
            wdir_tgl_10=[10, 20, 30, 40],
            wind_tgl_10=[1, 2, 3, 4],
            prediction_timestamp=datetime(2023, 2, 21, 18),
        ),
        ModelRunGridSubsetPrediction(
            tmp_tgl_2=[1, 2, 3, 4],
            rh_tgl_2=[20, 30, 40, 50],
            apcp_sfc_0=[3, 6, 3, 4],
            wdir_tgl_10=[280, 290, 300, 310],
            wind_tgl_10=[5, 6, 7, 8],
            prediction_timestamp=datetime(2023, 2, 21, 21),
        ),
        ModelRunGridSubsetPrediction(
            tmp_tgl_2=[1, 2, 3, 4],
            rh_tgl_2=None,
            apcp_sfc_0=[3, 6, 3, 4],
            wdir_tgl_10=[20, 30, 40, 50],
            wind_tgl_10=[4, 3, 2, 1],
            prediction_timestamp=datetime(2023, 2, 21, 21),
        ),
    ]
    return result


def mock_get_stations(*args):
    """Mocked out listing of weather stations"""
    return [
        WeatherStation(
            code=123,
            name="Test",
            lat=50.7,
            long=-120.425,
            ecodivision_name="Test",
            core_season=Season(start_month=5, start_day=1, end_month=9, end_day=21),
        ),
    ]


def mock_get_processed_file_count(*args):
    """Mocked out get processed file count"""
    return 162


def mock_get_processed_file_record(called: bool):
    if called:
        return ProcessedModelRunUrl()
    called = True
    return None


geom = (
    "POLYGON ((-120.525 50.77500000000001, -120.375 50.77500000000001,-120.375 50.62500000000001,"
    " -120.525 50.62500000000001, -120.525 50.77500000000001))"
)
shape = wkt.loads(geom)
