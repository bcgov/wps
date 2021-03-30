Feature: /stations/

    Scenario: Get weather stations from WFWX
        Given I request a list of weather stations
        Then the response status code is <status>
        And there are at least 60 active weather stations
        And there is a station in <index> has <code>, <name>, <lat> and <long>
        And the station has <ecodivision_name> with <core_season>

        Examples:
            | status | index | code | name         | lat       | long        | ecodivision_name                 | core_season                                                        |
            | 200    | 0     | 1142 | 14G (CRD)    | 49.55     | -124.3625   | COOL HYPERMARITIME AND HIGHLANDS | {"start_month": 5, "start_day": 15, "end_month": 8, "end_day": 31} |
            | 200    | 1     | 543  | 31N (CRD)    | 45.5297   | -123.6375   | COOL HYPERMARITIME AND HIGHLANDS | {"start_month": 5, "start_day": 15, "end_month": 8, "end_day": 31} |
