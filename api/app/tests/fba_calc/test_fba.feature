Feature: /fbc/

    Scenario: Fire Behaviour Calculation
        # NOTE: When writing requests, we already have stubs in place for the following station combinations:
        # (230,), (146,230), (322,346,335)
        # NOTE: When
        Given I received a fba-calc <request_json>
        Then the response status code is <status_code>
        And the response is <response_json>

        Examples:
            | request_json               | status_code | response_json                       |
            | c2_request.json            | 200         | None                                |
            | c3_request.json            | 200         | fba_calc/c3_response.json           |
            | c4_request.json            | 200         | None                                |
            | c5_request.json            | 200         | None                                |
            | c6_7mcbh_request.json      | 200         | fba_calc/c6_7mcbh_response.json     |
            | c6_2mcbh_request.json      | 200         | None                                |
            | c7_request.json            | 200         | None                                |
            | d1_request.json            | 200         | None                                |
            | m1_75conifer_request.json  | 200         | None                                |
            | m1_50conifer_request.json  | 200         | None                                |
            | m1_25conifer_request.json  | 200         | None                                |
            | m2_75conifer_request.json  | 200         | None                                |
            | m2_50conifer_request.json  | 200         | None                                |
            | m2_25conifer_request.json  | 200         | None                                |
            | m3_30deadfir_request.json  | 200         | None                                |
            | m3_60deadfir_request.json  | 200         | None                                |
            | m3_100deadfir_request.json | 200         | None                                |
            | m4_30deadfir_request.json  | 200         | None                                |
            | m4_60deadfir_request.json  | 200         | None                                |
            | m4_100deadfir_request.json | 200         | None                                |
            | o1a_0curing_request.json   | 200         | fba_calc/o1a_0curing_response.json  |
            | o1a_30curing_request.json  | 200         | fba_calc/o1a_30curing_response.json |
            | o1a_90curing_request.json  | 200         | fba_calc/o1a_90curing_response.json |
            | o1b_0curing_request.json   | 200         | None                                |
            | o1b_30curing_request.json  | 200         | None                                |
            | o1b_90curing_request.json  | 200         | None                                |
            | s1_request.json            | 200         | None                                |
            | s2_request.json            | 200         | None                                |
            | s3_request.json            | 200         | None                                |