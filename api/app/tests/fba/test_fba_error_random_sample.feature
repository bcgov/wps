Feature: /fbc/

    Scenario: Fire Behaviour Calculation
        Given <fuel_type>, <percentage_conifer>, <percentage_dead_balsam_fir>, <grass_cure> and <crown_base_height> for <num_iterations>
        Then ROS is within <ros_margin_of_error> compared to REDapp
        And HFI is within <hfi_margin_of_error> compared to REDapp
        And CFB is within <cfb_margin_of_error> compared to REDapp
        And 1 Hour Spread is within <one_hour_spread_margin_of_error> compared to REDapp

        Examples:
            | fuel_type | percentage_conifer | percentage_dead_balsam_fir | grass_cure | crown_base_height | ros_margin_of_error | hfi_margin_of_error | cfb_margin_of_error | one_hour_spread_margin_of_error | num_iterations |
            | C1        | 100                | None                       | None       | 2                 | 0.01                | 0.01                | 0.03                | 0.01                            | 20             |
            | C2        | 100                | None                       | None       | 3                 | 0.01                | 0.07                | 0.41                | 0.41                            | 20             |
            | C3        | 100                | None                       | None       | 8                 | 0.01                | 0.06                | 0.20                | 0.15                            | 20             |
            | C4        | 100                | None                       | None       | 8                 | 0.01                | 0.12                | 1.0                 | 0.02                            | 20             |
            | C5        | 100                | None                       | None       | 8                 | 0.01                | 0.67                | 1.0                 | 0.03                            | 20             |
            | C6        | 100                | None                       | None       | 8                 | 0.24                | 0.22                | 0.01                | 0.47                            | 20             |
            | C7        | 100                | None                       | None       | 8                 | 0.01                | 0.02                | 0.07                | 0.02                            | 20             |
            | D1        | 100                | None                       | None       | None              | 0.01                | 0.01                | 0.01                | 0.01                            | 20             |
            | M1        | 75                 | None                       | None       | 6                 | 0.01                | 0.02                | 0.08                | 0.02                            | 20             |
            | M1        | 50                 | None                       | None       | 6                 | 0.01                | 0.07                | 0.43                | 0.37                            | 20             |
            | M1        | 25                 | None                       | None       | 6                 | 0.01                | 0.21                | 7.00                | 0.42                            | 20             |
            | M2        | 75                 | None                       | None       | 6                 | 0.01                | 0.02                | 0.10                | 0.02                            | 20             |
            | M2        | 50                 | None                       | None       | 6                 | 0.01                | 0.09                | 0.71                | 0.34                            | 20             |
            | M2        | 25                 | None                       | None       | 6                 | 0.01                | 0.02                | 0.15                | 0.05                            | 20             |
            | M3        | None               | 30                         | None       | 6                 | 0.01                | 0.01                | 0.03                | 0.01                            | 20             |
            | M3        | None               | 60                         | None       | 6                 | 0.01                | 0.18                | 2.2                 | 0.70                            | 20             |
            | M3        | None               | 100                        | None       | 6                 | 0.01                | 0.23                | 1.6                 | 0.45                            | 20             |
            | M4        | None               | 30                         | None       | 6                 | 0.01                | 0.02                | 0.37                | 0.35                            | 20             |
            | M4        | None               | 60                         | None       | 6                 | 0.01                | 0.09                | 0.04                | 0.01                            | 20             |
            | M4        | None               | 100                        | None       | 6                 | 0.01                | 0.02                | 1.0                 | 0.12                            | 20             |
            | O1A       | None               | None                       | 25         | None              | 0.01                | 0.01                | 0.01                | 0.01                            | 20             |
            | O1A       | None               | None                       | 50         | None              | 0.01                | 0.01                | 0.01                | 0.01                            | 20             |
            | O1A       | None               | None                       | 100        | None              | 0.01                | 0.01                | 0.01                | 0.01                            | 20             |
            | O1B       | None               | None                       | 25         | None              | 0.01                | 0.01                | 0.01                | 0.01                            | 20             |
            | O1B       | None               | None                       | 50         | None              | 0.01                | 0.01                | 0.01                | 0.01                            | 20             |
            | O1B       | None               | None                       | 100        | None              | 0.01                | 0.01                | 0.01                | 0.01                            | 20             |
            | S1        | None               | None                       | None       | None              | 0.01                | 0.01                | 0.01                | 0.01                            | 20             |
            | S2        | None               | None                       | None       | None              | 0.01                | 0.01                | 0.01                | 0.01                            | 20             |
            | S3        | None               | None                       | None       | None              | 0.01                | 0.01                | 0.01                | 0.01                            | 20             |
