"""Tests for rocketchat_notifications.py"""

from wps_shared.chatops_notification import send_chatops_notification


def test_rocketchat_notifications():
    response = send_chatops_notification(
        "This is an automated unit test for rocketchat_notifications.",
        Exception("General exception message"),
    )
    assert response["success"] == True
