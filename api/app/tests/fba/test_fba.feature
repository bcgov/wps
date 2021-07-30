Feature: /fbc/

    Scenario: Fire Behaviour Calculation
        # NOTE: When writing requests, we already have stubs in place for the following station combinations:
        # (230,), (146,230), (322,346,335)
        # NOTE: When
        Given I received a <request_json>
        Then the response status code is <status_code>
        And the response is <response_json>

        Examples:
            | request_json                       | status_code | response_json                       |
            | json/c1_request.json               | 200         | json/c1_response.json               |
            | json/c1_request_no_daily_data.json | 200         | json/c1_response_no_daily_data.json |
            | json/c1_request_forecast.json      | 200         | json/c1_response_forecast.json      |
            | json/c1_request_multiple.json      | 200         | json/c1_response_multiple.json      |
            | json/c2_request.json               | 200         |                                     |
            | json/c3_request.json               | 200         | json/c3_response.json               |
            | json/c4_request.json               | 200         |                                     |
            | json/c5_request.json               | 200         |                                     |
            | json/c6_7mcbh_request.json         | 200         | json/c6_7mcbh_response.json         |
            | json/c6_2mcbh_request.json         | 200         |                                     |
            | json/c7_request.json               | 200         |                                     |
            | json/d1_request.json               | 200         |                                     |
            | json/m1_75conifer_request.json     | 200         |                                     |
            | json/m1_50conider_request.json     | 200         |                                     |
            | json/m1_25confier_request.json     | 200         |                                     |
            | json/m2_75confier_request.json     | 200         |                                     |
            | json/m2_50confier_request.json     | 200         |                                     |
            | json/m2_25confier_request.json     | 200         |                                     |
            | json/m3_30deadfir_request.json     | 200         |                                     |
            | json/m3_60deadfir_request.json     | 200         |                                     |
            | json/m3_100deadfir_request.json    | 200         |                                     |
            | json/m4_30deadfir_request.json     | 200         |                                     |
            | json/m4_60deadfir_request.json     | 200         |                                     |
            | json/m4_100deadfir_request.json    | 200         |                                     |
            | json/o1a_0curing_request.json      | 200         | json/o1a_0curing_response.json      |
            | json/o1a_30curing_request.json     | 200         | json/o1a_30curing_response.json     |
            | json/o1a_90curing_request.json     | 200         | json/o1a_90curing_response.json     |
            | json/o1b_0curing_request.json      | 200         |                                     |
            | json/o1b_30curing_request.json     | 200         |                                     |
            | json/o1b_90curing_request.json     | 200         |                                     |
            | json/s1_request.json               | 200         |                                     |
            | json/s2_request.json               | 200         |                                     |
            | json/s3_request.json               | 200         |                                     |