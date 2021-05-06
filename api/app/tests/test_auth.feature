Feature: Authentication

    Scenario: Handling unauthenticated users
        Given I am an unauthenticated user <token> when I <verb> a protected <endpoint>
        Then I will get an error with <status> code
        And Unauthenticated access audit logs are created

        Examples:
            | token        | status | endpoint                                          | verb |
            | Basic token  | 401    | /api/weather_models/GDPS/predictions/summaries/   | post |
            | just_token   | 401    | /api/weather_models/GDPS/predictions/summaries/   | post |
            | Bearer token | 401    | /api/weather_models/GDPS/predictions/summaries/   | post |
            | just_token   | 401    | /api/weather_models/GDPS/predictions/most_recent/ | post |
            | Bearer token | 401    | /api/weather_models/GDPS/predictions/most_recent/ | post |
            | just_token   | 401    | /api/stations/details/                            | get  |

    Scenario: Verifying authenticated users
        Given <utc_time>
        Given I am an authenticated user when I <verb> a protected <endpoint>
        Then I shouldn't get an unauthorized error <status> code
        And Authenticated access audit logs are created

        Examples:
            | status | endpoint                                          | verb | utc_time      |
            | 200    | /api/weather_models/GDPS/predictions/summaries/   | post | 1618870929583 |
            | 200    | /api/weather_models/GDPS/predictions/most_recent/ | post | 1618870929583 |
            | 200    | /api/stations/details/                            | get  | 1618870929583 |
