Feature: /stations/

    Scenario: Get weather stations
        Given USE_WFWX=<use_wfwx>
        Given I request a list of weather stations from <url> with <authentication>
        Then the response status code is <status>
        And there are at least 200 active weather stations
        And there is a station with <code>, <name>, <lat> and <long>

        Examples:
            | url            | status | code | name         | lat        | long         | use_wfwx | authentication |
            | /api/stations/ | 200    | 1142 | 14G (CRD)    | 48.494444  | -123.613889  | True     |                |
            | /api/stations/ | 200    | 322  | AFTON        | 50.6733333 | -120.4816667 | True     |                |
            | /api/stations/ | 200    | 317  | ALLISON PASS | 49.0623139 | -120.7674194 | False    |                |

    Scenario: Get detailed weather stations
        Given A <crud_mapping>
        Given <utc_time>
        Given I request a list of weather stations from <url> with <authentication>
        Then the response status code is <status>
        Then the expected response is <expected_response>

        Examples:
            | url                    | status | expected_response                            | crud_mapping                     | utc_time      | authentication |
            | /api/stations/details/ | 200    | test_stations_details_expected_response.json | test_stations_crud_mappings.json | 1618870929583 | True           |


