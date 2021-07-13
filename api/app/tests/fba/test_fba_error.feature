Feature: /fbc/

    Scenario: Fire Behaviour Calculation
        # NOTE: When writing requests, we already have stubs in place for the following station combinations:
        # (230,), (146,230), (322,346,335)
        Given <elevation>, <latitude>, <longitude>, <time_of_interest>, <wind_speed>, <wind_direction>, <percentage_conifer>, <percentage_dead_balsam_fir>, <grass_cure>, <crown_base_height>, <isi>, <bui>, <ffmc>, <dmc>, <dc>, <fuel_type>
        Then ROS is within <spreadsheet_error_margin> of <spreadsheet_ros>
        Then CFB is within <spreadsheet_error_margin> of <spreadsheet_cfb>
        Then HFI is within <spreadsheet_error_margin> of <spreadsheet_hfi>
        And ROS is within <red_app_error_margin> of REDapp ROS
        And CFB is within <red_app_error_margin> of REDapp CFB
        And HFI is within <red_app_error_margin> of REDapp HFI

        Examples:
            | elevation | latitude   | longitude    | time_of_interest | wind_speed | wind_direction | percentage_conifer | percentage_dead_balsam_fir | grass_cure | crown_base_height | fuel_type | isi  | bui   | ffmc | dmc   | dc    | red_app_error_margin | spreadsheet_error_margin | spreadsheet_ros | spreadsheet_hfi | spreadsheet_cfb |
            | 780       | 50.6733333 | -120.4816667 | 2021-07-12       | 6.2        | 3              | 100                | None                       | None       | 2                 | C1        | 11.5 | 186.8 | 94.8 | 126.1 | 900.3 | 0.07                 | 0.18                     | 5.22            | 2590.68         | 0.6             |

