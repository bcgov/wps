import pytest

from wps_weather_data import weather_data_addresser as addresser_module
from wps_weather_data.weather_data_addresser import WeatherDataAddresser


def addresser_for(monkeypatch, suffix):
    settings = {"OBJECT_STORE_BUCKET": "some-bucket", "SUFFIX": suffix}
    monkeypatch.setattr(addresser_module.config, "get", settings.get)
    return WeatherDataAddresser()


@pytest.mark.parametrize("suffix", ["prod", None, ""])
def test_production_and_local_use_the_production_root(monkeypatch, suffix):
    addresser = addresser_for(monkeypatch, suffix)

    assert addresser.get_runs_key() == "weather/stations/runs"
    assert addresser.get_by_time_key() == "weather/stations/by_time"
    assert addresser.get_staging_key("GDPS") == "weather/stations/staging/gdps"
    assert addresser.get_grid_key("HRDPS", "recent") == "weather/grids/hrdps/recent"


def test_dev_deployment_keeps_its_own_copy(monkeypatch):
    addresser = addresser_for(monkeypatch, "pr-123")

    assert addresser.get_runs_key() == "dev/pr-123/weather/stations/runs"
    assert addresser.get_by_time_key() == "dev/pr-123/weather/stations/by_time"
    assert addresser.get_staging_key("RDPS") == "dev/pr-123/weather/stations/staging/rdps"
    assert addresser.get_grid_key("RDPS", "history") == "dev/pr-123/weather/grids/rdps/history"


def test_delta_uri(monkeypatch):
    addresser = addresser_for(monkeypatch, "pr-123")

    assert addresser.delta_uri(addresser.get_runs_key()) == (
        "s3://some-bucket/dev/pr-123/weather/stations/runs"
    )
