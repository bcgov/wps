Feature: Noon calculator

    Scenario: Calculate noon data
        Given <data>
        When processed
        Then <timestamp> <temperature> <relative_humidity> <delta_precipitation>

        Examples:
            | data                                                                                                                                                                                                                                                                | timestamp                 | temperature       | relative_humidity  | delta_precipitation |
            | ({'datetime': '2020-07-21T18:00:00+00:00', 'values': {'temperature': 1.0, 'relative_humidity': 10.0, 'delta_precipitation': 10.0}}, {'datetime': '2020-07-21T21:00:00+00:00', 'values':{'temperature': 3.0, 'relative_humidity': 30, 'delta_precipitation': 20.0}}) | 2020-07-21T20:00:00+00:00 | 2.333333333333333 | 23.333333333333336 | 16.666666666666668  |
            | ({'datetime': '2020-07-21T19:00:00+00:00', 'values': {'temperature': 1.0, 'relative_humidity': 10.0, 'delta_precipitation': 10.0}}, {'datetime': '2020-07-21T21:00:00+00:00', 'values':{'temperature': 3.0, 'relative_humidity': 30, 'delta_precipitation': 40.0}}) | 2020-07-21T20:00:00+00:00 | 2                 | 20                 | 25                  |
