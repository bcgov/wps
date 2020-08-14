Feature: /models/{model}/predictions/

    Scenario: Get model prediction summaries from database
        Given A database
        Given station <codes>
        When I call <endpoint>
        Then The <expected_response> is matched
        Examples:
            | codes | endpoint                            | expected_response                               |
            | [322] | /models/GDPS/predictions/summaries/ | test_models_predictions_summaries_response.json |
