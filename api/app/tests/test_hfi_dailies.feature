Feature: /hfi-calc/daily

    Scenario: Get metrics for stations
        Given I request metrics for all stations beginning at time <start_time_stamp> and ending at time <end_time_stamp>.
        Then the response status code is <status_code>
        And the response has status <status> and temperature <temperature> and relative humidity <relative_humidity>, and wind_direction <wind_direction> and wind_speed <wind_speed> and precipitation <precipitation> and grass_cure_percentage <grass_cure_percentage> and ffmc <ffmc> and dc <dc> and <dmc> and isi <isi> and <bui> and fwi <fwi> and danger_cl <danger_cl>

        Examples:
            | status_code | start_time_stamp | end_time_stamp | status   | temperature | relative_humidity | wind_direction | wind_speed | precipitation | grass_cure_percentage | ffmc | dc  | dmc | isi | bui | fwi | danger_cl |
            | 200         | 0                | 1              | Observed | 1.0         | 1.0               | 1.0            | 1.0        | 1.0           | 1.0                   | 1.0  | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0       |


