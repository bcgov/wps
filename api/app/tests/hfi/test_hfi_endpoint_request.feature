Feature: /hfi/

    Scenario: HFI - request
        # In this scenario, we expect a request to be loaded from the database - but there isn't one.
        Given I have a stored request <stored_request_json>
        And I spy on store_hfi_request
        And I received a hfi-calc <url> with <verb>
        Then the response status code is <status_code>
        And the response is <response_json>
        And the response isn't cached
        And request == saved = <request_saved>

        Examples:
            | url                                                                                              | verb | status_code | response_json                                            | request_saved | stored_request_json                   |
            | /api/hfi-calc/fire_centre/1                                                                      | get  | 200         | hfi/test_hfi_endpoint_load_response.json                 | False         | None                                  |
            | /api/hfi-calc/fire_centre/1                                                                      | get  | 200         | hfi/test_hfi_endpoint_load_response.json                 | False         | test_hfi_endpoint_stored_request.json |
            | /api/hfi-calc/fire_centre/1/2020-05-21                                                           | get  | 200         | hfi/test_hfi_endpoint_load_response.json                 | False         | None                                  |
            | /api/hfi-calc/fire_centre/1/2020-05-21                                                           | get  | 200         | hfi/test_hfi_endpoint_load_response.json                 | False         | test_hfi_endpoint_stored_request.json |
            # Test set fire start range
            | /api/hfi-calc/fire_centre/1/2020-05-21/planning_area/1/fire_starts/2020-05-21/fire_start_range/2 | post | 200         | hfi/test_hfi_endpoint_response_set_fire_start_range.json | True          | None                                  |
            | /api/hfi-calc/fire_centre/1/2020-05-21/planning_area/1/fire_starts/2020-05-21/fire_start_range/2 | post | 200         | hfi/test_hfi_endpoint_response_set_fire_start_range.json | True          | test_hfi_endpoint_stored_request.json |
            # Test the station selection.
            | /api/hfi-calc/fire_centre/1/2020-05-21/planning_area/1/station/230/selected/false                | post | 200         | hfi/test_hfi_endpoint_response_deselect_station.json     | True          | None                                  |
            | /api/hfi-calc/fire_centre/1/2020-05-21/planning_area/1/station/230/selected/false                | post | 200         | hfi/test_hfi_endpoint_response_deselect_station.json     | True          | test_hfi_endpoint_stored_request.json |
            | /api/hfi-calc/fire_centre/1/2020-05-21/planning_area/1/station/230/selected/true                 | post | 200         | hfi/test_hfi_endpoint_response_select_station.json       | True          | None                                  |
            | /api/hfi-calc/fire_centre/1/2020-05-21/planning_area/1/station/230/selected/true                 | post | 200         | hfi/test_hfi_endpoint_response_select_station.json       | True          | test_hfi_endpoint_stored_request.json |
            # Test start + end date
            | /api/hfi-calc/fire_centre/1/2020-05-21/2020-05-26                                                | post | 200         | hfi/test_hfi_endpoint_set_date_range_response.json       | True          | None                                  |
            | /api/hfi-calc/fire_centre/1/2020-05-21/2020-05-26                                                | post | 200         | hfi/test_hfi_endpoint_set_date_range_response.json       | True          | test_hfi_endpoint_stored_request.json |
    # pdf


    Scenario: HFI - pdf download
        Given I received a hfi-calc request url:<url> verb:<verb> request:<request_json>
        Then the response status code is <status_code>
        And the response isn't cached

        Examples:
            # TODO: These test currently exposes a "bug" in the code where removing a station from one area, means it's removed from all.
            | url                        | verb | request_json                   | status_code |
            # Test perfect scenario, we have 2 stations, they're both selected, and they have data for all days.
            | /api/hfi-calc/download-pdf | post | test_hfi_endpoint_request.json | 200         |