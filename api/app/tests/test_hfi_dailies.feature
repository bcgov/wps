Feature: /hfi-calc/daily

    Scenario: Get metrics for stations
        Given I request metrics for all stations beginning at time <start_time_stamp> and ending at time <end_time_stamp>.
        Then the response status code is <status_code>
        And the response has status <status>
        And <temperature>
        And <relative_humidity>
        And <wind_direction>
        And <wind_speed>
        And <precipitation>
        And <grass_cure_percentage>
        And <ffmc>
        And <dc>
        And <dmc>
        And <isi>
        And <bui>
        And <fwi>
        And <danger_class>

        Examples:
            | status_code | start_time_stamp | end_time_stamp | status   | temperature | relative_humidity | wind_direction | wind_speed | precipitation | grass_cure_percentage | ffmc | dc  | dmc | isi | bui | fwi | danger_class |
            | 200         | 0                | 1              | Observed | 1.0         | 1.0               | 1.0            | 1.0        | 1.0           | 1.0                   | 1.0  | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0          |


