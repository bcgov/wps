Feature: /hfi/

    Scenario: HFI - request
        # In this scenario, we expect a request to be loaded from the database - but there isn't one.
        Given I received a hfi-calc <url> <request_json> with <verb>
        Then the response status code is <status_code>
        And the response is <response_json>

        Examples:
            # TODO: These test currently exposes a "bug" in the code where removing a station from one area, means it's removed from all.
            | url                                                                                              | verb | request_json                                            | status_code | response_json                                                |
            # Test perfect scenario, we have 2 stations, they're both selected, and they have data for all days.
            | /api/hfi-calc/                                                                                   | post | test_hfi_endpoint_request.json                          | 200         | hfi/test_hfi_endpoint_response.json                          |
            # # Test scenario where we have 1 station selected, one station deselected, and data for all days.
            | /api/hfi-calc/                                                                                   | post | test_hfi_endpoint_request_1_of_2_stations_selected.json | 200         | hfi/test_hfi_endpoint_response_1_of_2_stations_selected.json |
            # # Test less than ideal scenario, we have 2 stations, they're both selected, one of them is missing data for one day.
            | /api/hfi-calc/                                                                                   | post | test_hfi_endpoint_request_missing_data.json             | 200         | hfi/test_hfi_endpoint_response_missing_data.json             |
            # # Test load request scenario
            | /api/hfi-calc/fire_centre/1/2020-05-21                                                           | get  | None                                                    | 200         | hfi/test_hfi_endpoint_load_response.json                     |
            # Test set fire start range
            | /api/hfi-calc/fire_centre/1/2020-05-21/planning_area/1/fire_starts/2020-05-21/fire_start_range/2 | post | None                                                    | 200         | hfi/test_hfi_endpoint_response_set_fire_start_range.json     |
