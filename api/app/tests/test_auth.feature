Feature: Authentication

    Scenario: Handling unauthenticated users
        Given I'm mocking
        Given I am an unauthenticated user <token> when I access a protected <endpoint>
        Then I will get an error with <status> code
        And I will see an error <message>
        And Assert called

        Examples:
            | token        | status | message                                                 | endpoint                                          |
            | Basic token  | 401    | Could not validate the credential (Not enough segments) | /api/weather_models/GDPS/predictions/summaries/   |
            | just_token   | 401    | Could not validate the credential (Not enough segments) | /api/weather_models/GDPS/predictions/summaries/   |
            | Bearer token | 401    | Could not validate the credential (Not enough segments) | /api/weather_models/GDPS/predictions/summaries/   |
            | just_token   | 401    | Could not validate the credential (Not enough segments) | /api/weather_models/GDPS/predictions/most_recent/ |
            | Bearer token | 401    | Could not validate the credential (Not enough segments) | /api/weather_models/GDPS/predictions/most_recent/ |

    Scenario: Verifying authenticated users
        Given I am an authenticated user when I access a protected <endpoint>
        Then I shouldn't get an unauthorized error <status> code

        Examples:
            | status | endpoint                                          |
            | 200    | /api/weather_models/GDPS/predictions/summaries/   |
            | 200    | /api/weather_models/GDPS/predictions/most_recent/ |
