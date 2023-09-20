Feature: /fbc/

    Scenario: Fire Behaviour Calculation
        # NOTE: When writing requests, we already have stubs in place for the following station combinations:
        # (230,), (146,230), (322,346,335)
        # NOTE: When
        Given I received a fba-calc <request_json>
        Then the response status code is <status_code>
        And the response is <response_json>

        Examples:
            | request_json    | status_code | response_json |
            | s1_request.json | 200         | None          |
            | s2_request.json | 200         | None          |
            | s3_request.json | 200         | None          |