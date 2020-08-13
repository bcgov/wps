Feature: /models/{model}/forecasts/

    Scenario: Get model forecasts from database
        Given A database with <data>
        Given station <codes>
        When I call <endpoint>
        Then There are <num_forecast_values>
        Then The <expected_response> is matched
        Examples:
            | codes | endpoint                | data                          | num_forecast_values  | expected_response                      |
            | [322] | /models/GDPS/forecasts/ | test_models_forecasts_db.json | {'index':0, 'len':3} | test_models_forecasts_db_response.json |
