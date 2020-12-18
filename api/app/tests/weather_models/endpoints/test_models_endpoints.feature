Feature: Generic model endpoint testing

    Scenario: Generic model endpoint testing
        Given some explanatory <notes>
        Given A <crud_mapping>
        Given station <codes>
        When I call <endpoint>
        Then The <expected_status_code> is matched
        Then The <expected_response> is matched
        Examples:
            | codes      | endpoint                                  | crud_mapping                                                           | expected_status_code | expected_response                                                 | notes                                                                                                            |
            | [322]      | /api/models/GDPS/predictions/summaries/   | test_models_predictions_summaries_crud_mappings.json                   | 200                  | test_models_predictions_summaries_response.json                   |                                                                                                                  |
            | [322, 838] | /api/models/GDPS/predictions/summaries/   | test_models_predictions_summaries_multiple_crud_mappings.json          | 200                  | test_models_predictions_summaries_response_multiple.json          |                                                                                                                  |
            | [838]      | /api/models/GDPS/predictions/most_recent/ | test_models_predictions_most_recent_GDPS_[838]_crud_mappings.json      | 200                  | test_models_predictions_most_recent_GDPS_[838]_response.json      |                                                                                                                  |
            | [838, 209] | /api/models/GDPS/predictions/most_recent/ | test_models_predictions_most_recent_RDPS_[838, 209]_crud_mappings.json | 200                  | test_models_predictions_most_recent_RDPS_[838, 209]_response.json |                                                                                                                  |
            | [956]      | /api/models/GDPS/predictions/most_recent/ | test_models_predictions_most_recent_GDPS_[956]_crud_mappings.json      | 200                  | test_models_predictions_most_recent_GDPS_[956]_response.json      | Testing for rare case, where model run time matches prediction time, and previous precip delta is not available. |
