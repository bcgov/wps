Feature: /models/{model}/predictions/

    Scenario: Get model predictions from database
        Given A database with <data>
        Given station <codes>
        When I call <endpoint>
        Then There are <num_prediction_values>
        Then The <expected_response> is matched
        Examples:
            | codes | endpoint                      | data                            | num_prediction_values | expected_response                        |
            | [322] | /api/models/GDPS/predictions/ | test_models_predictions_db.json | {'index':0, 'len':3}  | test_models_predictions_db_response.json |
