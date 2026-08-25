from wps_shared.db.models.weather_models import ProcessedModelRunUrl
from wps_shared.schemas.stations import Season, WeatherStation

class MockResponse:
    """Mocked out request.Response object"""

    def __init__(self, status_code, content=None):
        self.status_code = status_code
        self.content = content


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
