Feature: /stations/

    Scenario: Get weather stations from WFWX
        Given I request a list of weather stations
        Then the response status code is <status>
        And there are at least 200 active weather stations
        And there is a station in <index> has <code>, <name>, <lat> and <long>

        Examples:
            | status | index | code | name         | lat       | long        | 
            | 200    | 0     | 1142 | 14G (CRD)    | 49.55     | -124.3625   |
            | 200    | 3     | 322  | AFTON        | 50.673333 | -120.481666 | 

        
        