Feature: Generic model endpoint testing

    Scenario: Generic model endpoint testing
        Given A <sql_response> for <crud_method> in <module>
        Given station <codes>
        When I call <endpoint>
        Then The <expected_status_code> is matched
        Then The <expected_response> is matched
        Examples:
            | codes      | endpoint                                  | sql_response                                                 | crud_method                                                 | module                               | expected_status_code | expected_response                                                 |
            | [322]      | /api/models/GDPS/predictions/summaries/   | test_models_predictions_summaries_sql_response.json          | get_station_model_predictions_order_by_prediction_timestamp | app.weather_models.fetch.summaries   | 200                  | test_models_predictions_summaries_response.json                   |
            | [322, 838] | /api/models/GDPS/predictions/summaries/   | test_models_predictions_summaries_sql_response_multiple.json | get_station_model_predictions_order_by_prediction_timestamp | app.weather_models.fetch.summaries   | 200                  | test_models_predictions_summaries_response_multiple.json          |
            | [838]      | /api/models/GDPS/predictions/most_recent/ | test_models_predictions_most_recent_GDPS_[838]_db.json       | get_station_model_predictions                               | app.weather_models.fetch.predictions | 200                  | test_models_predictions_most_recent_GDPS_[838]_response.json      |
            | [838, 209] | /api/models/GDPS/predictions/most_recent/ | test_models_predictions_most_recent_RDPS_[838, 209]_db.json  | get_station_model_predictions                               | app.weather_models.fetch.predictions | 200                  | test_models_predictions_most_recent_RDPS_[838, 209]_response.json |
