Feature: /models/{model}/forecasts/

    Scenario: Get model forecast summaries from database
        Given A database
        Given station <codes>
        When I call <endpoint>
        Then The <expected_response> is matched
        Examples:
            | codes | endpoint                          | expected_response                             |
            | [322] | /models/GDPS/forecasts/summaries/ | test_models_forecasts_summaries_response.json |
