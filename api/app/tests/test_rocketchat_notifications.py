"""Tests for rocketchat_notifications.py"""

from wps_shared.rocketchat_notifications import send_rocketchat_notification


def test_rocketchat_notifications():
    response = send_rocketchat_notification("This is an automated unit test for rocketchat_notifications.", Exception("General exception message"))
    assert response["success"] == True
