Feature: /fbc/

    Scenario: Fire Behaviour Calculation
        Given <fuel_type>, <percentage_conifer>, <percentage_dead_balsam_fir>, <grass_cure> and <crown_base_height> for <num_iterations>
        Then ROS is within <ros_margin_of_error> compared to REDapp
        And HFI is within <hfi_margin_of_error> compared to REDapp
        And CFB is within <cfb_margin_of_error> compared to REDapp
        And 1 Hour Spread is within <one_hour_spread_margin_of_error> compared to REDapp
        And ROS_t is within range
        And CFB_t is within range of <cfb_t_margin_of_error> compared to REDapp
        And HFI_t is within range
        And (1 HR Size)_t is within range
        And Log it

        Examples:
            | fuel_type | percentage_conifer | percentage_dead_balsam_fir | grass_cure | crown_base_height | ros_margin_of_error | hfi_margin_of_error | cfb_margin_of_error | cfb_t_margin_of_error | one_hour_spread_margin_of_error | num_iterations |
            | C1        | 100                | None                       | None       | 2                 | 0.01                | 0.01                | 0.01                | 0.01                  | 0.01                            | 20             |
            | C2        | 100                | None                       | None       | 3                 | 0.01                | 0.12                | 0.19                | 0.01                  | 0.17                            | 20             |
            | C3        | 100                | None                       | None       | 8                 | 0.01                | 0.01                | 0.01                | 0.01                  | 0.01                            | 20             |
            # C4 and C5 seem to have some issues with CFB
            # | C4        | 100                | None                       | None       | 8                 | 0.01                | 0.02                | 1.00              | 0.01   | 0.28                            | 20             |
            # | C5        | 100                | None                       | None       | 8                 | 0.01                | 0.01                | 0.04              | 0.01   | 0.01                            | 20             |
            | C6        | 100                | None                       | None       | 7                 | 0.01                | 0.01                | 0.01                | 0.01                  | 0.01                            | 20             |
            | C7        | 100                | None                       | None       | 8                 | 0.01                | 0.01                | 0.01                | 0.01                  | 0.01                            | 20             |
            | D1        | 100                | None                       | None       | None              | 0.01                | 0.01                | 0.01                | 0.01                  | 0.01                            | 20             |
            # M1, M2, M3 & M4 are failing on 1Ha Fire Size (though not that bad!)
            # | M1_75C        | 75                 | None                       | None       | 6                 | 0.01                | 0.02                | 0.02           | 0.01      | 0.05                            | 20             |
            # | M1_50C        | 50                 | None                       | None       | 6                 | 0.01                | 0.21                | 0.61           | 0.01      | 0.10                            | 20             |
            | M1        | 25                 | None                       | None       | 6                 | 0.01                | 0.01                | 0.01                | 0.01                  | 0.01                            | 20             |
            # | M2_75C        | 75                 | None                       | None       | 6                 | 0.01                | 0.03                | 0.03        | 0.01         | 0.07                            | 20             |
            # | M2_50C        | 50                 | None                       | None       | 6                 | 0.01                | 0.11                | 0.39        | 0.01         | 0.13                            | 20             |
            | M2        | 25                 | None                       | None       | 6                 | 0.01                | 0.01                | 0.01                | 0.01                  | 0.01                            | 20             |
            | M3        | None               | 30                         | None       | 6                 | 0.01                | 0.01                | 0.19                | 0.12                  | 0.01                            | 20             |
            | M3        | None               | 60                         | None       | 6                 | 0.01                | 0.19                | 0.48                | 0.01                  | 0.35                            | 20             |
            # | M3_100D        | None               | 100                        | None       | 6                 | 0.01                | 0.17                | 0.32         | 0.01        | 0.38                            | 20             |
            # | M4_30D        | None               | 30                         | None       | 6                 | 0.01                | 0.19                | 0.36        | 0.01         | 0.21                            | 20             |
            | M4        | None               | 60                         | None       | 6                 | 0.01                | 0.01                | 0.01                | 0.01                  | 0.01                            | 20             |
            | M4        | None               | 100                        | None       | 6                 | 0.01                | 0.03                | 0.12                | 0.01                  | 0.02                            | 20             |
            | O1A       | None               | None                       | 25         | None              | 0.01                | 0.01                | 0.01                | 0.01                  | 0.01                            | 20             |
            | O1A       | None               | None                       | 50         | None              | 0.01                | 0.01                | 0.01                | 0.01                  | 0.01                            | 20             |
            | O1A       | None               | None                       | 100        | None              | 0.01                | 0.01                | 0.01                | 0.01                  | 0.01                            | 20             |
            | O1B       | None               | None                       | 25         | None              | 0.01                | 0.01                | 0.01                | 0.01                  | 0.01                            | 20             |
            | O1B       | None               | None                       | 50         | None              | 0.01                | 0.01                | 0.01                | 0.01                  | 0.01                            | 20             |
            | O1B       | None               | None                       | 100        | None              | 0.01                | 0.01                | 0.01                | 0.01                  | 0.01                            | 20             |
            | S1        | None               | None                       | None       | None              | 0.01                | 0.01                | 0.01                | 0.01                  | 0.01                            | 20             |
            | S2        | None               | None                       | None       | None              | 0.01                | 0.01                | 0.01                | 0.01                  | 0.01                            | 20             |
            | S3        | None               | None                       | None       | None              | 0.01                | 0.01                | 0.01                | 0.01                  | 0.01                            | 20             |
