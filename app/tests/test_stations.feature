Feature: /stations/

    Scenario: Get weather stations from WFWX
        Given I request a list of weather stations
        Then the response status code is <status>
        And there are active 16 weather stations
        And there is a station in <index> has <code>, <name>, <lat>, and <long>

        Examples:
            | status | index | code | name         | lat     | long        |
            | 200    | 0     | 67   | HAIG CAMP    | 49.3806 | -121.525967 |
            | 200    | 1     | 72   | UBC RESEARCH | 49.2645 | -122.573283 |
