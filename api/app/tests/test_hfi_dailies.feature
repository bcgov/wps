Feature: /hfi-calc/daily

    Scenario: Get metrics for stations
        Given I request metrics for all stations beginning at time <start_time_stamp> and ending at time <end_time_stamp> with <fuel_type_abbrev> and <grass_cure_percentage>.
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
        And <head_fire_intensity>
        And <rate_of_spread>
        And <fire_type>

        Examples:
            | status_code | start_time_stamp | end_time_stamp | status | temperature | relative_humidity | wind_direction | wind_speed | precipitation | grass_cure_percentage | ffmc | dc  | dmc | isi | bui | fwi | danger_class | fuel_type_abbrev | head_fire_intensity    | fire_type | rate_of_spread         |
            | 200         | 0                | 1              | ACTUAL | 1.0         | 1.0               | 1.0            | 1.0        | 1.0           | 1.0                   | 1.0  | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0          | C7B              | 6.455516194707674e-24  | SUR       | 7.209078465552808e-25  |
            | 200         | 0                | 1              | ACTUAL | 1.0         | 1.0               | 1.0            | 1.0        | 1.0           |                       | 1.0  | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0          | C7B              |                        |           |                        |
            | 200         | 0                | 1              | ACTUAL | 1.0         | 1.0               | 1.0            | 1.0        | 1.0           | 1.0                   | 1.0  | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0          | C7               | 0.00011611553969925833 | SUR       | 1.2966988409822604e-05 |


