Feature: /fba/fire-centres

    Scenario: Get fire centres with their stations
        Given I request all fire centres
        Then the response status code is <status>
        And the response contains the list of fire centers

        Examples:
            | status |
            | 200    | 