Feature: Forecast

    Scenario: Create a single forecast
        Given I am a session creating a forecast with <date_time>, <temperature>, <rh>, <wind_speed>, <total_precip> at time <issue_date> for station <station_code>
        Then The forecast should be committed to the database

        Examples:
            | issue_date                 | date_time                  | temperature | rh | wind_speed | total_precip | station_code |
            | 2020-06-02 05:42:08.811091 | 2020-06-02 00:00:00.000000 | 10          | 50 | 13         | 2.1          | 45           |
            | 2020-06-01 15:42:08.811091 | 2020-06-02 00:00:00.000000 | 27          | 90 | 30         | 0.0          | 45           |
