Feature: /stations/

    Scenario: Get weather stations from WFWX
        Given I request a list of weather stations
        Then the response status code is <status>
        And there are active 16 weather stations
        And there is a station in <index> has <code>, <name>, <lat> and <long>
        And the station has <ecodivision_name> with <core_season>

        Examples:
            | status | index | code | name         | lat     | long        | ecodivision_name                 | core_season                                                        |
            | 200    | 0     | 67   | HAIG CAMP    | 49.3806 | -121.525967 | COOL HYPERMARITIME AND HIGHLANDS | {"start_month": 5, "start_day": 15, "end_month": 8, "end_day": 31} |
            | 200    | 1     | 72   | UBC RESEARCH | 49.2645 | -122.573283 | COOL HYPERMARITIME AND HIGHLANDS | {"start_month": 5, "start_day": 15, "end_month": 8, "end_day": 31} |
