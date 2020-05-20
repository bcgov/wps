Feature: /forecasts/

    Scenario: Get forecasts from spotwx
        Given I request weather forecasts for stations: <codes>
        Then the response status code is <status>
        And there are <num_forecasts> from two stations
        And there are 10 days of forecasts for each station
        And forecasts have noon values only
        And forecast values should be interpolated

        Examples:
            | codes      | status | num_forecasts |
            | [331, 328] | 200    | 2             |
            | [331]      | 200    | 1             |
