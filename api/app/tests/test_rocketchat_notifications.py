""" BDD tests for rocketchat_notifications.py """
from pytest_bdd import scenario, given, then
from app.rocketchat_notifications import send_rocketchat_notification


@scenario('test_rocketchat_notifications.feature', 'Send automated notification to Rocketchat channel')
def test_rocketchat_notifications():
    """  BDD Scenario. """


@given('a specified <message_string> and an <exception>')
def response(message_string, exception: str):
    """ Send the message to the Rocketchat channel using configured auth. """
    return send_rocketchat_notification(message_string, Exception(exception))


@then('the response should indicate success <success_boolean>')
# pylint: disable=redefined-outer-name
def assert_success_boolean(response, success_boolean):
    """ Assert the value in the response json for key 'success' matches success_boolean """
    assert str(response['success']) == success_boolean
