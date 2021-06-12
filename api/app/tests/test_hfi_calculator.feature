Feature: /hfi-calc/

    Scenario: Get fire centres, planning areas, and weather stations
        Given I request all fire centres, planning areas, etc.
        Then the response status code is <status>
        And there are at least <num_weather_stations> weather stations
        And the station with index <index> has code <code>, named <station_name>, with fuel type <fuel_type> and elevation <elevation>, assigned to planning area <planning_area_name> and fire centre <fire_centre_name>

        Examples:
            | status | num_weather_stations | index | code | station_name | fuel_type | elevation | planning_area_name | fire_centre_name     |
            | 200    | 15                   | 0     | 322  | AFTON        | O1B       | 780       | Kamloops (K2)      | Kamloops Fire Centre |
            | 200    | 15                   | 6     | 346  | SALMON ARM   | C7        | 527       | Vernon (K4)        | Kamloops Fire Centre |

    