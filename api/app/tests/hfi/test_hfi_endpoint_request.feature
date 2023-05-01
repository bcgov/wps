Feature: /hfi/

    Scenario: HFI - GET request
        Given I have a stored request <stored_request_json>
        And I spy on store_hfi_request
        And I received a GET request for hfi-calc <url>
        Then the response status code is <status_code>
        And the response is <response_json>
        And the response isn't cached
        And request == saved = <request_saved>

        Examples:
            | url                                               | status_code | response_json                            | request_saved | stored_request_json                   |
            | /api/hfi-calc/fire_centre/1                       | 200         | hfi/test_hfi_endpoint_load_response.json | False         | None                                  |
            | /api/hfi-calc/fire_centre/1                       | 200         | hfi/test_hfi_endpoint_load_response.json | False         | test_hfi_endpoint_stored_request.json |
            | /api/hfi-calc/fire_centre/1/2020-05-21/2020-05-25 | 200         | hfi/test_hfi_endpoint_load_response.json | False         | None
            | /api/hfi-calc/fire_centre/1/2020-05-21/2020-05-25 | 200         | hfi/test_hfi_endpoint_load_response.json | False         | test_hfi_endpoint_stored_request.json |


            # pdf
            | api/hfi-calc/fire_centre/1/2020-05-21/2020-05-25/pdf | 200 | None | False | None                                  |
            | api/hfi-calc/fire_centre/1/2020-05-21/2020-05-25/pdf | 200 | None | False | test_hfi_endpoint_stored_request.json |


    Scenario: HFI - POST request
        Given I have a stored request <stored_request_json>
        And I spy on store_hfi_request
        And I received a POST request for hfi-calc <url> with <role>
        Then the response status code is <status_code>
        And the response is <response_json>
        And the response isn't cached
        And request == saved = <request_saved>

        Examples:
            | url                                                                                                         | role                | status_code | response_json                                            | request_saved | stored_request_json                   |
            # Test set fire start range with correct role
            | /api/hfi-calc/fire_centre/1/2020-05-21/2020-05-25/planning_area/1/fire_starts/2020-05-21/fire_start_range/2 | hfi_set_fire_starts | 200         | hfi/test_hfi_endpoint_response_set_fire_start_range.json | True          | None                                  |
            | /api/hfi-calc/fire_centre/1/2020-05-21/2020-05-25/planning_area/1/fire_starts/2020-05-21/fire_start_range/2 | hfi_set_fire_starts | 200         | hfi/test_hfi_endpoint_response_set_fire_start_range.json | True          | test_hfi_endpoint_stored_request.json |
            # Test set fire start range without roles
            | /api/hfi-calc/fire_centre/1/2020-05-21/2020-05-25/planning_area/1/fire_starts/2020-05-21/fire_start_range/2 | None                | 401         | None                                                     | False         | None                                  |
            | /api/hfi-calc/fire_centre/1/2020-05-21/2020-05-25/planning_area/1/fire_starts/2020-05-21/fire_start_range/2 | None                | 401         | None                                                     | False         | test_hfi_endpoint_stored_request.json |
            # Test set fire start range without correct role
            | /api/hfi-calc/fire_centre/1/2020-05-21/2020-05-25/planning_area/1/fire_starts/2020-05-21/fire_start_range/2 | hfi_select_station  | 401         | None                                                     | False         | None                                  |
            | /api/hfi-calc/fire_centre/1/2020-05-21/2020-05-25/planning_area/1/fire_starts/2020-05-21/fire_start_range/2 | hfi_select_station  | 401         | None                                                     | False         | test_hfi_endpoint_stored_request.json |
            # Test the station selection with correct role
            | /api/hfi-calc/fire_centre/1/2020-05-21/2020-05-25/planning_area/1/station/230/selected/false                | hfi_select_station  | 200         | hfi/test_hfi_endpoint_response_deselect_station.json     | True          | None                                  |
            | /api/hfi-calc/fire_centre/1/2020-05-21/2020-05-25/planning_area/1/station/230/selected/false                | hfi_select_station  | 200         | hfi/test_hfi_endpoint_response_deselect_station.json     | True          | test_hfi_endpoint_stored_request.json |
            | /api/hfi-calc/fire_centre/1/2020-05-21/2020-05-25/planning_area/1/station/230/selected/true                 | hfi_select_station  | 200         | hfi/test_hfi_endpoint_response_select_station.json       | True          | None                                  |
            | /api/hfi-calc/fire_centre/1/2020-05-21/2020-05-25/planning_area/1/station/230/selected/true                 | hfi_select_station  | 200         | hfi/test_hfi_endpoint_response_select_station.json       | True          | test_hfi_endpoint_stored_request.json |
            # Test the station selection without roles
            | /api/hfi-calc/fire_centre/1/2020-05-21/2020-05-25/planning_area/1/station/230/selected/false                | None                | 401         | None                                                     | False         | None                                  |
            | /api/hfi-calc/fire_centre/1/2020-05-21/2020-05-25/planning_area/1/station/230/selected/false                | None                | 401         | None                                                     | False         | test_hfi_endpoint_stored_request.json |
            | /api/hfi-calc/fire_centre/1/2020-05-21/2020-05-25/planning_area/1/station/230/selected/true                 | None                | 401         | None                                                     | False         | None                                  |
            | /api/hfi-calc/fire_centre/1/2020-05-21/2020-05-25/planning_area/1/station/230/selected/true                 | None                | 401         | None                                                     | False         | test_hfi_endpoint_stored_request.json |
            # Test the station selection without correct role
            | /api/hfi-calc/fire_centre/1/2020-05-21/2020-05-25/planning_area/1/station/230/selected/false                | hfi_set_fire_starts | 401         | None                                                     | False         | None                                  |
            | /api/hfi-calc/fire_centre/1/2020-05-21/2020-05-25/planning_area/1/station/230/selected/false                | hfi_set_fire_starts | 401         | None                                                     | False         | test_hfi_endpoint_stored_request.json |
            | /api/hfi-calc/fire_centre/1/2020-05-21/2020-05-25/planning_area/1/station/230/selected/true                 | hfi_set_fire_starts | 401         | None                                                     | False         | None                                  |
            | /api/hfi-calc/fire_centre/1/2020-05-21/2020-05-25/planning_area/1/station/230/selected/true                 | hfi_set_fire_starts | 401         | None                                                     | False         | test_hfi_endpoint_stored_request.json |
            # Test set the station fuel type with correct role
            | /api/hfi-calc/fire_centre/1/2020-05-21/2020-05-25/planning_area/1/station/230/fuel_type/2                   | hfi_set_fuel_type   | 200         | hfi/test_hfi_endpoint_response_set_fuel_type.json        | True          | None                                  |
            | /api/hfi-calc/fire_centre/1/2020-05-21/2020-05-25/planning_area/1/station/230/fuel_type/2                   | hfi_set_fuel_type   | 200         | hfi/test_hfi_endpoint_response_set_fuel_type.json        | True          | test_hfi_endpoint_stored_request.json |
            # Test set the station fuel type without correct role
            | /api/hfi-calc/fire_centre/1/2020-05-21/2020-05-25/planning_area/1/station/230/fuel_type/2                   | None                | 401         | None                                                     | False         | None                                  |
            | /api/hfi-calc/fire_centre/1/2020-05-21/2020-05-25/planning_area/1/station/230/fuel_type/2                   | None                | 401         | None                                                     | False         | test_hfi_endpoint_stored_request.json |
            # Invalid fuel type should return 500 error, and not be saved.
            | /api/hfi-calc/fire_centre/1/2020-05-21/2020-05-25/planning_area/1/station/230/fuel_type/-1                  | hfi_set_fuel_type   | 500         | None                                                     | False         | None                                  |

