""" BDD tests for rocketchat_notifications.py """
from pytest_bdd import scenario, given, then, parsers
from app.rocketchat_notifications import send_rocketchat_notification


@scenario('test_rocketchat_notifications.feature', 'Send automated notification to Rocketchat channel')
def test_rocketchat_notifications():
    """  BDD Scenario. """


@given(parsers.parse('a specified {message_string} and an {exception}'), target_fixture='response')
def given_message(message_string: str, exception: str):
    """ Send the message to the Rocketchat channel using configured auth. """
    return send_rocketchat_notification(message_string, Exception(exception))


@then(parsers.parse('the response should indicate success {success_boolean}'))
def assert_success_boolean(response, success_boolean):
    """ Assert the value in the response json for key 'success' matches success_boolean """
    assert str(response['success']) == success_boolean
