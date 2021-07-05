Feature: /fbc/

    Scenario: Fire Behaviour Calculation
        # NOTE: When writing requests, we already have stubs in place for the following station combinations:
        # (230,), (146,230), (322,346,335)
        Given I received a <request_json>
        Then the response status code is <status_code>
        And the response is <response_json>

        Examples:
            | request_json    | status_code | response_json    |
            | c1_request.json | 200         | c1_response.json |
# | c2_request.json            | 200         | c2_response.json            |
# | c3_request.json            | 200         | c3_response.json            |
# | c4_request.json            | 200         | c4_response.json            |
# | c5_request.json            | 200         | c5_response.json            |
# | c6_7mcbh_request.json      | 200         | c6_7mcbh_response.json      |
# | c6_2mcbh_request.json      | 200         | c6_2mcbh_response.json      |
# | c7_request.json            | 200         | c7_response.json            |
# | d1_request.json            | 200         | d1_response.json            |
# | d2_request.json            | 200         | d2_response.json            |
# | m1_75conifer_request.json  | 200         | m1_75conifer_response.json  |
# | m1_50conider_request.json  | 200         | m1_50conifer_response.json  |
# | m1_25confier_request.json  | 200         | m1_25conifer_response.json  |
# | m2_75confier_request.json  | 200         | m2_75conifer_response.json  |
# | m2_50confier_request.json  | 200         | m2_50conifer_response.json  |
# | m2_25confier_request.json  | 200         | m2_25conifer_response.json  |
# | m3_30deadfir_request.json  | 200         | m3_30deadfir_response.json  |
# | m3_60deadfir_request.json  | 200         | m3_60deadfir_response.json  |
# | m3_100deadfir_request.json | 200         | m3_100deadfir_response.json |
# | m4_30deadfir_request.json  | 200         | m4_30deadfir_response.json  |
# | m4_60deadfir_request.json  | 200         | m4_60deadfir_response.json  |
# | m4_100deadfir_request.json | 200         | m4_100deadfir_response.json |
# | o1a_0curing_request.json   | 200         | o1a_0curing_response.json   |
# | o1a_30curing_request.json  | 200         | o1a_30curing_response.json  |
# | o1a_90curing_request.json  | 200         | o1a_90curing_response.json  |
# | o1b_0curing_request.json   | 200         | o1b_0curing_response.json   |
# | o1b_30curing_request.json  | 200         | o1b_30curing_response.json  |
# | o1b_90curing_request.json  | 200         | o1b_90curing_response.json  |
# | s1_request.json            | 200         | s1_response.json            |
# | s2_request.json            | 200         | s2_response.json            |