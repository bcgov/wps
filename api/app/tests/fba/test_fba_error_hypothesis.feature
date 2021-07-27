Feature: /fbc/

    Scenario: Fire Behaviour Calculation
        Given <fuel_type>, <percentage_conifer>, <percentage_dead_balsam_fir>, <grass_cure> and <crown_base_height> for <num_iterations>
        Then ROS is within <ros_margin_of_error> compared to REDapp
        And HFI is within <hfi_margin_of_error> compared to REDapp
        And CFB is within <cfb_margin_of_error> compared to REDapp
        And 1 Hour Spread is within <one_hour_spread_margin_of_error> compared to REDapp

        Examples:
            | fuel_type | percentage_conifer | percentage_dead_balsam_fir | grass_cure | crown_base_height | ros_margin_of_error | hfi_margin_of_error | cfb_margin_of_error | one_hour_spread_margin_of_error | num_iterations |
            # | C1        | 100                | None                       | None       | 2                 | 0.01                | 0.01                | 0.03                | 0.01                            | 20             |
            # | C2        | 100                | None                       | None       | 3                 | 0.01                | 0.07                | 0.01                | 0.41                            | 20             |
            | C3        | 100                | None                       | None       | 8                 | 0.01                | 0.01                | 0.01                | 0.01                            | 20             |
