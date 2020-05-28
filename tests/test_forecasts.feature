Feature: /forecasts/

    Scenario: Get forecasts from spotwx
        Given I request weather forecasts for stations: <codes>
        Then the response status code is <status>
        And there are <num_forecasts> from two stations
        And there are 3 hourly forecast with 10 days of interpolated noon values for each station
        And forecast values should be interpolated

        Examples:
            | codes      | status | num_forecasts |
            | [331, 328] | 200    | 2             |
            | [331]      | 200    | 1             |
