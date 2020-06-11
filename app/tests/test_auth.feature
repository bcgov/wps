Feature: Authentication

    Scenario: Handling unauthenticated users
        Given I am an unauthenticated user <token> when I access a protected endpoint
        Then I will get an error with <status> code
        And I will see an error <message>

        Examples:
            | token        | status | message                                                 |
            | Basic token  | 401    | Not authenticated                                       |
            | just_token   | 401    | Not authenticated                                       |
            | Bearer token | 401    | Could not validate the credential (Not enough segments) |

    Scenario: Verifying authenticated users
        Given I am an authenticated user when I access a protected endpoint
        Then I shouldn't get an unauthorized error <status> code

        Examples:
            | status |
            | 200    |
