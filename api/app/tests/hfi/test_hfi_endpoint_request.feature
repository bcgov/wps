Feature: /hfi/

    Scenario: HFI - request
        Given I have a stored request <stored_request_json>
        And I spy on store_hfi_request
        And I received a hfi-calc <url> with <verb>
        Then the response status code is <status_code>
        And the response is <response_json>
        And the response isn't cached
        And request == saved = <request_saved>

        Examples:
            | url                                                                               | verb | status_code | response_json                                        | request_saved | stored_request_json                   |
            | /api/hfi-calc/fire_centre/1                                                       | get  | 200         | hfi/test_hfi_endpoint_load_response.json             | False         | None                                  |
            | /api/hfi-calc/fire_centre/1                                                       | get  | 200         | hfi/test_hfi_endpoint_load_response.json             | False         | test_hfi_endpoint_stored_request.json |
            | /api/hfi-calc/fire_centre/1/2020-05-21                                            | get  | 200         | hfi/test_hfi_endpoint_load_response.json             | False         | None                                  |
            | /api/hfi-calc/fire_centre/1/2020-05-21                                            | get  | 200         | hfi/test_hfi_endpoint_load_response.json             | False         | test_hfi_endpoint_stored_request.json |
            # Test the station selection.
            | /api/hfi-calc/fire_centre/1/2020-05-21/planning_area/1/station/230/selected/false | post | 200         | hfi/test_hfi_endpoint_response_deselect_station.json | True          | None                                  |
            | /api/hfi-calc/fire_centre/1/2020-05-21/planning_area/1/station/230/selected/false | post | 200         | hfi/test_hfi_endpoint_response_deselect_station.json | True          | test_hfi_endpoint_stored_request.json |
            | /api/hfi-calc/fire_centre/1/2020-05-21/planning_area/1/station/230/selected/true  | post | 200         | hfi/test_hfi_endpoint_response_select_station.json   | True          | None                                  |
            | /api/hfi-calc/fire_centre/1/2020-05-21/planning_area/1/station/230/selected/true  | post | 200         | hfi/test_hfi_endpoint_response_select_station.json   | True          | test_hfi_endpoint_stored_request.json |
            # Test start + end date
            | /api/hfi-calc/fire_centre/1/2020-05-21/2020-05-26                                 | post | 200         | hfi/test_hfi_endpoint_set_date_range_response.json   | True          | None                                  |
            | /api/hfi-calc/fire_centre/1/2020-05-21/2020-05-26                                 | post | 200         | hfi/test_hfi_endpoint_set_date_range_response.json   | True          | test_hfi_endpoint_stored_request.json |
            # pdf
            | api/hfi-calc/fire_centre/1/2020-05-21/pdf                                         | get  | 200         | None                                                 | False         | None                                  |
            | api/hfi-calc/fire_centre/1/2020-05-21/pdf                                         | get  | 200         | None                                                 | False         | test_hfi_endpoint_stored_request.json |

    Scenario: HFI - request set fire starts with role
        Given I have a stored request <stored_request_json>
        And I spy on store_hfi_request
        And I received a hfi-calc <url> with <verb>
        Then the response status code is <status_code>
        And the response is <response_json>
        And the response isn't cached
        And request == saved = <request_saved>

        Examples:
            | url                                                                                              | verb | status_code | response_json                                            | request_saved | stored_request_json                   |
            | /api/hfi-calc/fire_centre/1/2020-05-21/planning_area/1/fire_starts/2020-05-21/fire_start_range/2 | post | 200         | hfi/test_hfi_endpoint_response_set_fire_start_range.json | True          | None                                  |
            | /api/hfi-calc/fire_centre/1/2020-05-21/planning_area/1/fire_starts/2020-05-21/fire_start_range/2 | post | 200         | hfi/test_hfi_endpoint_response_set_fire_start_range.json | True          | test_hfi_endpoint_stored_request.json |

    Scenario: HFI - request set fire starts without role
        Given I have a stored request <stored_request_json>
        And I spy on store_hfi_request
        And I received a hfi-calc <url> with <verb>
        Then the response status code is <status_code>
        And the response is <response_json>

        Examples:
            | url                                                                                              | verb | status_code | response_json | stored_request_json |
            | /api/hfi-calc/fire_centre/1/2020-05-21/planning_area/1/fire_starts/2020-05-21/fire_start_range/2 | post | 401         | None          | None                |
            | /api/hfi-calc/fire_centre/1/2020-05-21/planning_area/1/fire_starts/2020-05-21/fire_start_range/2 | post | 401         | None          | None                |

    Scenario: HFI - pdf download
        # Very similar to the scenario above, except we don't bother with checking the response content.
        Given I have a stored request <stored_request_json>
        And I spy on store_hfi_request
        And I received a hfi-calc <url> with <verb>
        Then the response status code is <status_code>
        And the response isn't cached
        And request == saved = <request_saved>

        Examples:
            | url                                       | verb | status_code | request_saved | stored_request_json                   |
            | api/hfi-calc/fire_centre/1/2020-05-21/pdf | get  | 200         | False         | None                                  |
            | api/hfi-calc/fire_centre/1/2020-05-21/pdf | get  | 200         | False         | test_hfi_endpoint_stored_request.json |