Feature: Linear regression for weather

    Scenario: Learn weather
        Given An instance of StationMachineLearning
        When The machine learns
        Then The <model_temp> for <timestamp> results in <bias_adjusted_temp>
        And The <model_rh> for <timestamp> results in <bias_adjusted_rh>
        Examples:
            | model_temp | model_rh | timestamp                        | bias_adjusted_temp | bias_adjusted_rh |
            | 20         | 50       | 2020-09-03T21:14:51.939836+00:00 | 0                  | 0                |