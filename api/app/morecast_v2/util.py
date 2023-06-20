from app.schemas.morecast_v2 import WeatherIndeterminate
from typing import List


def actual_exists(transformed_forecast: WeatherIndeterminate, wf1_actuals: List[WeatherIndeterminate]):
    # Get actual weatherdeterminates with matching station code to the forecast, then see if any of those
    # actuals match the timestamp of the forecast
    station_code_matches = [actual for actual in wf1_actuals if actual.station_code ==
                            transformed_forecast.station_code]
    utc_timestamp_matches = [station_code_match for station_code_match in station_code_matches
                             if station_code_match.utc_timestamp == transformed_forecast.utc_timestamp]
    if len(utc_timestamp_matches):
        return True
    return False
