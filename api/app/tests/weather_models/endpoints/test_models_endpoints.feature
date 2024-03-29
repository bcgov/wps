Feature: Generic model endpoint testing

    Scenario: Generic model endpoint testing
        Given some explanatory <notes>
        Given A weather model crud mapping <crud_mapping>
        When I call <endpoint> with <codes>
        Then The status code = <expected_status_code>
        Then The response = <expected_response>
        Examples:
            | codes      | endpoint                                          | crud_mapping                                                           | expected_status_code | expected_response                                                 | notes                                                                                                            |
            | [322]      | /api/weather_models/GDPS/predictions/summaries/   | test_models_predictions_summaries_crud_mappings.json                   | 200                  | test_models_predictions_summaries_response.json                   | n/a                                                                                                              |
            | [322, 838] | /api/weather_models/GDPS/predictions/summaries/   | test_models_predictions_summaries_multiple_crud_mappings.json          | 200                  | test_models_predictions_summaries_response_multiple.json          | n/a                                                                                                              |
            | [838]      | /api/weather_models/GDPS/predictions/most_recent/ | test_models_predictions_most_recent_GDPS_[838]_crud_mappings.json      | 200                  | test_models_predictions_most_recent_GDPS_[838]_response.json      | n/a                                                                                                              |
            | [838, 209] | /api/weather_models/GDPS/predictions/most_recent/ | test_models_predictions_most_recent_RDPS_[838, 209]_crud_mappings.json | 200                  | test_models_predictions_most_recent_RDPS_[838, 209]_response.json | n/a                                                                                                              |
            | [956]      | /api/weather_models/GDPS/predictions/most_recent/ | test_models_predictions_most_recent_GDPS_[956]_crud_mappings.json      | 200                  | test_models_predictions_most_recent_GDPS_[956]_response.json      | Testing for rare case, where model run time matches prediction time, and previous precip delta is not available. |
