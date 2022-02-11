Feature: /hfi/

    # NOTE: When writing requests, we already have stubs in place for the following station combinations:
    # (230,),
    # NOTE: These combinations exist, but not for the mock dates:
    # (146,230), (322,346,335)

    Scenario: HFI - load request, no request stored
        # In this scenario, we expect a request to be loaded from the database - but there isn't one.
        Given I received a <request_json>, but don't have one stored
        Then the response status code is <status_code>
        And the response is <response_json>

        Examples:
            | request_json                        | status_code | response_json                                      |
            | test_hfi_endpoint_request_load.json | 200         | test_hfi_endpoint_response_request_not_loaded.json |

    Scenario: HFI - load request, request stored
        # In this scenario, we expect a request to be loaded from the database - and it's possible.
        Given I received a <request_json>, and have one stored <stored_request_json>
        Then the response status code is <status_code>
        And the response is <response_json>

        Examples:
            | request_json                        | status_code | response_json                                  | stored_request_json |
            | test_hfi_endpoint_request_load.json | 200         | test_hfi_endpoint_response_request_loaded.json | stored_request.json |