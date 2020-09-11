Feature: /models/{model}/predictions/historic/most_recent/

    Scenario: Get most recent historic model predictions from database for selected stations
        Given A database with <data>
        Given station <codes>
        Given starting date range of <start_date> 
        Given ending date range of <end_date>
        When I call <endpoint>
        Then There are <num_prediction_values>
        Then The <expected_response> is matched
        Examples:
            | codes | start_date               | end_date                 | endpoint                                       | data                                 | num_prediction_values | expected_response                                   |
            | [322] | "2020-08-30T06:00:00+00" | "2020-09-03T06:00:00+00" | /models/GDPS/predictions/historic/most_recent/ | test_historic_predictions_db.json    | {'index':0, 'len':3}  | test_most_recent_historic_predictions_response.json |
