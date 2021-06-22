Feature: /hfi-calc/fire-centres

    Scenario: Get fire centres, planning areas, and weather stations
        Given I request all fire centres, planning areas, etc.
        Then the response status code is <status>
        And there are at least <num_fire_centres> fire centres
        And each fire centre has at least 1 planning area
        And each planning area has at least 1 weather station
        And each weather station has a fuel_type assigned to it

        Examples:
            | status | num_fire_centres |
            | 200    | 1                |