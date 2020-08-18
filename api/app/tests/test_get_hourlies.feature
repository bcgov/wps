Feature: /hourlies/

    Scenario: Get hourlies
        Given I request hourlies for stations: <codes>
        Then the response status code is <status>
        And there are <num_groups> groups of hourlies
        And there are <num_readings_per_group> readings per group

        Examples:
            | codes      | status | num_groups | num_readings_per_group |
            | [146, 230] | 200    | 2          | [118, 118]             |
            | [230]      | 200    | 1          | [118]                  |