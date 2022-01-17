from app.wildfire_one.schema_parsers import parse_noon_forecast, parse_hourly_actual


def test_forecast_valid_flags_are_set():
    """ Noon forecast valid flags are set """
    raw_forecast = {
        "weatherTimestamp": 1,
        'updateDate': 1,
        "station_code": 1,
        "temperature": 1,
        "relativeHumidity": 1,
        "windSpeed": 1,
        "windDirection": 1,
        "precipitation": 1,
        "grasslandCuring": 1,
        "fineFuelMoistureCode": 1,
        "duffMoistureCode": 1,
        "droughtCode": 1,
        "initialSpreadIndex": 1,
        "buildUpIndex": 1,
        "fireWeatherIndex": 1,
        "dailySeverityRating": 1
    }

    result = parse_noon_forecast(1, raw_forecast)
    assert result.temp_valid is True
    assert result.rh_valid is True
    assert result.wspeed_valid is True
    assert result.wdir_valid is True
    assert result.precip_valid is True


def test_actual_valid_flags_are_set():
    """ Noon forecast valid flags are set """
    raw_hourly_actual = {
        "weatherTimestamp": 1,
        'updateDate': 1,
        "station_code": 1,
        "temperature": 1,
        "relativeHumidity": 1,
        "windSpeed": 1,
        "windDirection": 1,
        "precipitation": 1,
        "grasslandCuring": 1,
        "fineFuelMoistureCode": 1,
        "duffMoistureCode": 1,
        "droughtCode": 1,
        "initialSpreadIndex": 1,
        "buildUpIndex": 1,
        "fireWeatherIndex": 1,
        "dailySeverityRating": 1,
        "observationValidInd": True,
        "observationValidComment": ''
    }

    result = parse_hourly_actual(1, raw_hourly_actual)
    assert result.temp_valid is True
    assert result.rh_valid is True
    assert result.wspeed_valid is True
    assert result.wdir_valid is True
    assert result.precip_valid is True
