Feature: /noon_forecasts/summaries/
    Scenario: Get noon forecasts summaries(historic)
        Given I request noon forecasts for stations: <codes>
        Then the status code of the response is <status>
        And the response should have <num_summaries> summaries of forecasts
        And and contain calculated percentiles for available stations <codes>
        Examples:
            | codes      | status | num_summaries |
            | []         | 200    | 0             |
            | [999]      | 200    | 0             |
            | [322]      | 200    | 1             |
            | [209, 322] | 200    | 2             |