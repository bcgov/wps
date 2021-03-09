Feature: C-Haines endpoint testing

    Scenario: C-Haines endpoint testing
        Given A <crud_mapping>
        When I call <endpoint>
        Then I expect <status_code>
        Then The <expected_response> is matched
        Examples:
            | endpoint                                                                                                                                       | status_code | crud_mapping                              | expected_response                 |
            | /api/c-haines/GDPS/prediction?model_run_timestamp=2021-03-08T12%3A00%3A00&prediction_timestamp=2021-03-08T12%3A00%3A00&response_format=geoJSON | 200         | test_c_haines_endpoints_crud_mapings.json | prediction_expected_response.json |
            | /api/c-haines/model-runs                                                                                                                       | 200         | test_c_haines_endpoints_crud_mapings.json | model_runs_expected_response.json |
