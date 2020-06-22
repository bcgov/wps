Feature: /stations/

    Scenario: Get weather stations from WFWX
        Given I request a list of weather stations
        Then the response status code is <status>
        And there are active 16 weather stations
        And there is a station in <index> has <code>, <name>, <lat> and <long>
        And the station has <ecodivision_name> with core_season <start_month> <start_day> - <end_month> <end_day>

        Examples:
            | status | index | code | name         | lat     | long        | ecodivision_name                 | start_month | start_day | end_month | end_day |
            | 200    | 0     | 67   | HAIG CAMP    | 49.3806 | -121.525967 | COOL HYPERMARITIME AND HIGHLANDS | 5           | 15        | 8         | 31      |
            | 200    | 1     | 72   | UBC RESEARCH | 49.2645 | -122.573283 | COOL HYPERMARITIME AND HIGHLANDS | 5           | 15        | 8         | 31      |
