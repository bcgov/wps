Feature: C-Haines endpoint testing

    Scenario: C-Haines endpoint testing
        Given A <crud_mapping>
        When I call <endpoint>
        Then I expect <status_code>
        Then The <expected_response> is matched
        Examples:
            | endpoint                 | status_code | crud_mapping                              | expected_response                 |
            # | /api/c-haines/GDPS/predictions | 200         |
            | /api/c-haines/model-runs | 200         | test_c_haines_endpponts_crud_mapings.json | model_runs_expected_response.json |
# | codes | endpoint                       | crud_mapping                                         | expected_status_code | expected_response                               | notes |
# | [322] | /api/c-haines/GDPS/predictions | test_models_predictions_summaries_crud_mappings.json | 200                  | test_models_predictions_summaries_response.json |       |
# | [322, 838] | /api/weather_models/GDPS/predictions/summaries/   | test_models_predictions_summaries_multiple_crud_mappings.json          | 200                  | test_models_predictions_summaries_response_multiple.json          |                                                                                                                  |
# | [838]      | /api/weather_models/GDPS/predictions/most_recent/ | test_models_predictions_most_recent_GDPS_[838]_crud_mappings.json      | 200                  | test_models_predictions_most_recent_GDPS_[838]_response.json      |                                                                                                                  |
# | [838, 209] | /api/weather_models/GDPS/predictions/most_recent/ | test_models_predictions_most_recent_RDPS_[838, 209]_crud_mappings.json | 200                  | test_models_predictions_most_recent_RDPS_[838, 209]_response.json |                                                                                                                  |
# | [956]      | /api/weather_models/GDPS/predictions/most_recent/ | test_models_predictions_most_recent_GDPS_[956]_crud_mappings.json      | 200                  | test_models_predictions_most_recent_GDPS_[956]_response.json      | Testing for rare case, where model run time matches prediction time, and previous precip delta is not available. |
