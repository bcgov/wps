Feature: /hfi/

    Scenario: HFI - request
        # In this scenario, we expect a request to be loaded from the database - but there isn't one.
        Given I received a <request_json>
        Then the response status code is <status_code>
        And the response is <response_json>

        Examples:
            | request_json                   | status_code | response_json                   |
            # Test perfect scenario, we have 2 stations, they're both selected, and they have data for all days.
            | test_hfi_endpoint_request.json | 200         | test_hfi_endpoint_response.json |
# Test scenario where we have 1 station selected, one station deselected, and data for all days.
# Test less than ideal scenario, we have 2 stations, they're both selected, one of them is missing data for some days.
