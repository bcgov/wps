"""Run directly to preview the spot forecast email HTML in your browser.

    python -m app.smurfi.preview_email
"""
import subprocess
import tempfile
from datetime import datetime, timezone

from app.smurfi.email import build_spot_forecast_email


class _DW:
    def __init__(self, period, conditions, temperature, relative_humidity):
        self.period = period
        self.conditions = conditions
        self.temperature = temperature
        self.relative_humidity = relative_humidity


class _TW:
    def __init__(self, forecast_time, temperature, relative_humidity, wind, probability_of_precipitation, precipitation_amount):
        self.forecast_time = forecast_time
        self.temperature = temperature
        self.relative_humidity = relative_humidity
        self.wind = wind
        self.probability_of_precipitation = probability_of_precipitation
        self.precipitation_amount = precipitation_amount


class _SR:
    fire_number = ["V1234567"]
    requestor_name = "Darren Boss"
    geographic_description = "Strathcona"
    aspect = "East"
    elevation = 1100
    geom = None  # coord extraction falls back to "—" without a real DB geometry


class _SF:
    spot_request = _SR()
    issued_at = datetime(2026, 5, 25, 21, 30, tzinfo=timezone.utc)  # 1430 PDT
    expires_at = datetime(2026, 5, 27, 7, 0, tzinfo=timezone.utc)   # Wed May 27
    forecaster_name = "Conor Brady"
    forecaster_email = "conor.brady@gov.bc.ca"
    forecaster_phone = None
    synopsis = "A weak ridge of high pressure is maintaining mainly clear skies over the region."
    inversion_and_venting = "A surface inversion is expected tonight with poor venting conditions."
    outlook = "The ridge will weaken Thursday allowing a Pacific front to approach from the northwest."
    confidence = "High confidence. Models are in good agreement."
    fire_size = 2.5
    representative_station_codes = None
    descriptive_weather = [
        _DW("Today", "Mainly sunny in the morning then increasing afternoon cloud", 28, 18),
        _DW("Tonight", "Mainly clear", -2, 90),
        _DW("Tomorrow", "Cloudy", 12, 40),
    ]
    tabular_weather = [
        _TW(datetime(2026, 5, 25, 0, 0, tzinfo=timezone.utc), None, None, None, None, None),
        _TW(datetime(2026, 5, 25, 23, 0, tzinfo=timezone.utc), 28, 18, "SW 20-30", 5, 0),
        _TW(datetime(2026, 5, 26, 2, 0, tzinfo=timezone.utc), 25, 22, "SW 15", 5, 0),
        _TW(datetime(2026, 5, 26, 6, 0, tzinfo=timezone.utc), None, None, None, None, None),
        _TW(datetime(2026, 5, 26, 17, 0, tzinfo=timezone.utc), 12, 40, "W 10-20", 20, 2),
        _TW(datetime(2026, 5, 26, 20, 0, tzinfo=timezone.utc), 10, 55, "W 10", 20, 2),
        _TW(datetime(2026, 5, 26, 23, 0, tzinfo=timezone.utc), 8, 65, "Light", 30, 3),
        _TW(datetime(2026, 5, 27, 2, 0, tzinfo=timezone.utc), 6, 75, "Light", 30, 3),
        _TW(datetime(2026, 5, 27, 23, 0, tzinfo=timezone.utc), 14, 35, "NW 15", 10, 0),
    ]


if __name__ == "__main__":
    _, html_body = build_spot_forecast_email(_SF(), spot_detail_url="http://localhost:3000/smurfi/spots/1")

    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w") as f:
        f.write(html_body)
        path = f.name

    print(f"Preview written to: {path}")
    subprocess.run(["open", path])
