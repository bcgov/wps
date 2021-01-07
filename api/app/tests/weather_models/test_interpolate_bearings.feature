Feature: Interpolate bearings

    Scenario: Interpolate bearings
        Given <time_a>, <time_b>, <target_time>, <direction_a>, <direction_b>
        When You interpolate
        Then You get <result>
        Examples:
            | time_a                           | time_b                           | target_time                      | direction_a | direction_b | result             |
            # Test acute angle:
            | 2020-09-03T18:00:00.000000+00:00 | 2020-09-03T21:00:00.000000+00:00 | 2020-09-03T20:00:00.000000+00:00 | 10          | 20          | 16.666666666666668 |
            # Test obtuse angle:
            | 2020-09-03T18:00:00.000000+00:00 | 2020-09-03T21:00:00.000000+00:00 | 2020-09-03T20:00:00.000000+00:00 | 10          | 200         | 256.6666666666667  |
            # Test obtouse angle, interpolation in the other direction.
            | 2020-09-03T18:00:00.000000+00:00 | 2020-09-03T21:00:00.000000+00:00 | 2020-09-03T20:00:00.000000+00:00 | 200         | 10          | 313.3333333333333  |

