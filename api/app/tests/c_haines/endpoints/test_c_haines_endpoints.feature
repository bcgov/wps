Feature: C-Haines endpoint testing

    Scenario: C-Haines endpoint testing
        Given I call /api/c-haines <endpoint>
        Then the response status code is <status_code>
        Then The <expected_response> is matched
        Examples:
            | endpoint                                                                                                                                    | status_code | expected_response                                 |
            | /api/c-haines/GDPS/prediction?model_run_timestamp=2021-03-08T12%3A00%3A00&prediction_timestamp=2021-03-08T12%3A00%3A00&response_format=JSON | 307         | None                                              |
            | /api/c-haines/GDPS/prediction?model_run_timestamp=2021-03-08T12%3A00%3A00&prediction_timestamp=2021-03-08T12%3A00%3A00&response_format=KML  | 307         | None                                              |
            | /api/c-haines/model-runs                                                                                                                    | 200         | model_runs_expected_response.json                 |
            | /api/c-haines/GDPS/predictions?response_format=JSON                                                                                         | 501         | None                                              |
            | /api/c-haines/GDPS/predictions?response_format=KML                                                                                          | 200         | most_recent_predictions_kml_expected_response.kml |
            | /api/c-haines/GDPS/predictions?response_format=KML&model_run_timestamp=2021-06-08T12%3A00%3A00                                              | 200         | predictions_kml_expected_response.kml             |
            | /api/c-haines/network-link                                                                                                                  | 200         | network-link_response.kml                         |
