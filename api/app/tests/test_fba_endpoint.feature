Feature: /fba/fire-centres

    Scenario: Get fire centres with their stations
        Given I request all fire centres
        Then the response status code is <status>
        And the response contains the list of <expected_fire_centers>

        Examples:
            | status | expected_fire_centers               |
            | 200    | test_fba_endpoint_fire_centers.json |
