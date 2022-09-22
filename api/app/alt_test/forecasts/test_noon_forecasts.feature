Feature: /noon_forecasts/

    Scenario: Get noon_forecasts
        Given I request noon_forecasts for stations: <codes>
        Then the response status code is <status>
        And there are <num_groups> groups of forecasts

        Examples:
            | codes | status | num_groups |
            | [209] | 200    | 1          |