Feature: /fbc/

    Scenario: Fire Behaviour Calculation
        # NOTE: When writing requests, we already have stubs in place for the following station combinations:
        # (230,), (146,230), (322,346,335)
        # NOTE: When
        Given I received a fba-calc <request_json>
        Then the response status code is <status_code>
        And the response is <response_json>

        Examples:
            | request_json              | status_code | response_json                       |
            | o1a_0curing_request.json  | 200         | fba_calc/o1a_0curing_response.json  |
            | o1a_30curing_request.json | 200         | fba_calc/o1a_30curing_response.json |
            | o1a_90curing_request.json | 200         | fba_calc/o1a_90curing_response.json |
            | o1b_0curing_request.json  | 200         | None                                |
            | o1b_30curing_request.json | 200         | None                                |
            | o1b_90curing_request.json | 200         | None                                |
            | s1_request.json           | 200         | None                                |
            | s2_request.json           | 200         | None                                |
            | s3_request.json           | 200         | None                                |