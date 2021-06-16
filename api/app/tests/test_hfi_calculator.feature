# Feature: /hfi-calc/daily

#     Scenario: Get metrics for stations
#         Given I request metrics for all stations beginning at time <start_time_stamp> and ending at time <end_time_stamp>.
#         Then the response status code is <status_code>
#         And the status <status>, with temperature <temperature> and relative humidity <relative_humidity>, and wind_direction <wind_direction> and wind_speed <wind_speed> and precipitation <precipitation> and grass_cure_percentage <grass_cure_percentage> and ffmc <ffmc> and dc <dc> and <dmc> and isi <isi> and <bui> and fwi <fwi> and danger_cl <danger_cl> and fbp_fuel_type <fbp_fuel_type>

#         Examples:
#             | status_code | start_time_stamp | end_time_stamp | status   | temperature | relative_humidity | wind_direction | wind_speed | precipitation | grass_cure_percentage | ffmc | dc  | dmc | isi | bui | fwi | danger_cl | fbp_fuel_type |
#             | 200         | 0                | 1              | observed | 1.0         | 1.0               | 1.0            | 1.0        | 1.0           | 1.0                   | 1.0  | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0       | TBD           |

# Feature: /hfi-calc/

#     Scenario: Get fire centres, planning areas, and weather stations
#         Given I request all fire centres, planning areas, etc.
#         Then the response status code is <status>
#         And there are at least <num_fire_centres> fire centres
#         And each fire centre has at least 1 planning area
#         And each planning area has at least 1 weather station
#         And each weather station has a fuel_type assigned to it

#         Examples:
#             | status | num_fire_centres |
#             | 200    | 1                |


