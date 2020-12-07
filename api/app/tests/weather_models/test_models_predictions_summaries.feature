Feature: /models/{model}/predictions/

    Scenario: Get model prediction summaries from database
        Given A database <sql_response>
        Given station <codes>
        When I call <endpoint>
        Then The <expected_response> is matched
        Examples:
            | codes      | endpoint                                | sql_response                                                                          | expected_response                                        |
            | [322]      | /api/models/GDPS/predictions/summaries/ | app/tests/weather_models/test_models_predictions_summaries_sql_response.json          | test_models_predictions_summaries_response.json          |
            | [322, 838] | /api/models/GDPS/predictions/summaries/ | app/tests/weather_models/test_models_predictions_summaries_sql_response_multiple.json | test_models_predictions_summaries_response_multiple.json |
