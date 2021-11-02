Feature: /fba/fire-centres

    Scenario: Get fire centres with their stations
        Given I request all fire centres
        Then the response status code is <status>

        Examples:
            | status |
            | 200    | 