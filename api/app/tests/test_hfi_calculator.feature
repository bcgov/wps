Feature: /hfi-calc/daily

    Scenario: Get metrics for stations
        Given I request metrics for all stations beginning at time <start_time_stamp> and ending at time <end_time_stamp>.
        Then the response status code is <status>
        And the station with code <code>, with status <status>, with temperature <temperature> and relative humidity <relative_humidity>, and wind_direction <wind_direction> and wind_speed <wind_speed> and precipitation <precipitation> and grass_cure_percentage <grass_cure_percentage> and ffmc <ffmc> and dc <dc> and isi <isi> and fwi <fwi> and danger_cl <danger_cl> and fbp_fuel_type <fbp_fuel_type>

        Examples:
            | status | start_time_stamp | end_time_stamp | status   | temperature | relative_humidity | wind_direction | wind_speed | precipitation | grass_cure_percentage | ffmc | dc | isi | bui | fwi | danger_cl | fbp_fuel_type |
            | 200    | 15               | 0              | observed | 1           | 1                 | 1              | 1          | 1             | 1                     | 1    | 1  | 1   | 1   | 1   | 1         | 01A           |