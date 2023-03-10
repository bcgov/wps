from datetime import datetime
from app.schemas.stations import WeatherStation, Season
from shapely import wkt
from app.db.models.weather_models import (ProcessedModelRunUrl,
                                          ModelRunGridSubsetPrediction)


class MockResponse:
    """ Mocked out request.Response object """

    def __init__(self, status_code, content=None):
        self.status_code = status_code
        self.content = content


def mock_get_model_run_predictions(*args):
    result = [
        ModelRunGridSubsetPrediction(
            tmp_tgl_2=[2, 3, 4, 5],
            rh_tgl_2=[10, 20, 30, 40],
            apcp_sfc_0=[2, 4, 3, 6],
            wdir_tgl_10=[10, 20, 30, 40],
            wind_tgl_10=[1, 2, 3, 4],
            prediction_timestamp=datetime(2023, 2, 21, 18)),
        ModelRunGridSubsetPrediction(
            tmp_tgl_2=[1, 2, 3, 4],
            rh_tgl_2=[20, 30, 40, 50],
            apcp_sfc_0=[3, 6, 3, 4],
            wdir_tgl_10=[280, 290, 300, 310],
            wind_tgl_10=[5, 6, 7, 8],
            prediction_timestamp=datetime(2023, 2, 21, 21)),
        ModelRunGridSubsetPrediction(
            tmp_tgl_2=[1, 2, 3, 4],
            rh_tgl_2=None,
            apcp_sfc_0=[3, 6, 3, 4],
            wdir_tgl_10=[20, 30, 40, 50],
            wind_tgl_10=[4, 3, 2, 1],
            prediction_timestamp=datetime(2023, 2, 21, 21))
    ]
    return result


def mock_get_stations(*args):
    """ Mocked out listing of weather stations """
    return [WeatherStation(
        code=123, name='Test', lat=50.7, long=-120.425, ecodivision_name='Test',
        core_season=Season(
            start_month=5, start_day=1, end_month=9, end_day=21)), ]


def mock_get_processed_file_count(*args):
    """ Mocked out get processed file count """
    return 162


def mock_get_processed_file_record(called: bool):
    if called:
        return ProcessedModelRunUrl()
    called = True
    return None


geom = ("POLYGON ((-120.525 50.77500000000001, -120.375 50.77500000000001,-120.375 50.62500000000001,"
        " -120.525 50.62500000000001, -120.525 50.77500000000001))")
shape = wkt.loads(geom)
