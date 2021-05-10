Feature: Linear regression for weather

    Scenario: Learn weather
        Given An instance of StationMachineLearning for <coordinate> within <points>
        When The machine learns
        Then The <model_temp> for <timestamp> results in <bias_adjusted_temp>
        And The <model_rh> for <timestamp> results in <bias_adjusted_rh>
        And The <model_wind_speed> for <timestamp> results in <bias_adjusted_wind_speed>
        Examples:
            | model_temp | model_rh | model_wind_speed | timestamp                        | bias_adjusted_temp | bias_adjusted_rh | bias_adjusted_wind_speed | coordinate                 | points                                                                                                                                                                     |
            # using a timestamp with sample data, we should get some bias adjusted values:
            | 20         | 50       | 50               | 2020-09-03T21:14:51.939836+00:00 | 30                 | 100              | 2                        | [-120.4816667, 50.6733333] | [[-120.52499999999998, 50.775000000000006], [-120.37499999999997, 50.775000000000006], [-120.37499999999997, 50.62500000000001], [-120.52499999999998, 50.62500000000001]] |
            # using a timestamp without any samples, we should get None for the bias adjusted values:
            | 20         | 50       | 50               | 2020-09-03T01:14:51.939836+00:00 | None               | None             | None                     | [-120.4816667, 50.6733333] | [[-120.52499999999998, 50.775000000000006], [-120.37499999999997, 50.775000000000006], [-120.37499999999997, 50.62500000000001], [-120.52499999999998, 50.62500000000001]] |