Feature: Rocketchat Notifications

    Scenario: Send automated notification to Rocketchat channel
        Given a specified <message_string> and an <exception>
        Then the response should indicate success <success_boolean>

        Examples:
            | message_string                                               | exception                 | success_boolean |
            | This is an automated unit test for rocketchat_notifications. | General exception message | True            |