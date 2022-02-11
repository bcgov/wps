Feature: /hfi/

    Scenario: Head Fire Intensity Calculation
        # NOTE: When writing requests, we already have stubs in place for the following station combinations:
        # (230,), (146,230), (322,346,335)
        # NOTE: When
        Given I received a <request_json>
        Then the response status code is <status_code>
        And the response is <response_json>

        Examples:
            | request_json                     | status_code | response_json                     |
            | test_hfi_endpoint_request_1.json | 200         | test_hfi_endpoint_response_1.json |