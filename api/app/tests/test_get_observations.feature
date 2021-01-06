Feature: /observations/

    Scenario: Get hourly observations
        Given I request hourlies for stations: <codes> with <use_wfwx>
        Then the response status code is <status>
        And there are <num_groups> groups of hourlies
        And there are <num_readings_per_group> readings per group

        Examples:
            | codes      | status | num_groups | num_readings_per_group | use_wfwx |
            | [146, 230] | 200    | 2          | [118, 118]             | True     |
            | [230]      | 200    | 1          | [118]                  | True     |
            | [146, 230] | 200    | 2          | [1, 1]                 | False    |
            | [230]      | 200    | 1          | [1]                    | False    |