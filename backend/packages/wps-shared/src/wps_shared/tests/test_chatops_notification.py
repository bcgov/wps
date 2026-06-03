"""Tests for chatops_notification.py"""

from unittest.mock import MagicMock

import pytest
import requests

from wps_shared.chatops_notification import send_chatops_notification


@pytest.fixture
def mock_post(monkeypatch):
    mock = MagicMock()
    mock.return_value.json.return_value = {"success": True}
    monkeypatch.setattr(requests, "post", mock)
    return mock


def test_returns_response_json(mock_post):
    result = send_chatops_notification("test", Exception("err"))
    assert result == {"success": True}


def test_posts_to_chatops_url(mock_post):
    send_chatops_notification("test", Exception("err"))
    url = mock_post.call_args.args[0]
    assert url == "https://chat.ops/webhook/1"


def test_auth_header(mock_post):
    send_chatops_notification("test", Exception("err"))
    headers = mock_post.call_args.kwargs["headers"]
    assert headers["Authorization"] == "Bearer sometoken"


def test_body_contains_text(mock_post):
    send_chatops_notification("something went wrong", Exception("err"))
    body = mock_post.call_args.kwargs["json"]
    assert "something went wrong" in body["body"]


def test_body_severity(mock_post):
    send_chatops_notification("test", Exception("err"))
    body = mock_post.call_args.kwargs["json"]
    assert body["severity"] == "critical"


def test_body_url_label(mock_post):
    send_chatops_notification("test", Exception("err"))
    body = mock_post.call_args.kwargs["json"]
    assert body["urlLabel"] == "View Logs"


def test_body_pod_logs_url(monkeypatch, mock_post):
    monkeypatch.setenv("HOSTNAME", "wps-api-abc123")
    send_chatops_notification("test", Exception("err"))
    body = mock_post.call_args.kwargs["json"]
    assert body["url"] == "https://console.pathfinder.gov.bc.ca_8443/k8s/ns/project_namespace/pods/wps-api-abc123/logs"


def test_body_title_is_pod_name(monkeypatch, mock_post):
    monkeypatch.setenv("HOSTNAME", "wps-api-abc123")
    send_chatops_notification("test", Exception("err"))
    body = mock_post.call_args.kwargs["json"]
    assert body["title"] == "wps-api-abc123"


def test_returns_none_on_request_exception(monkeypatch):
    monkeypatch.setattr(requests, "post", MagicMock(side_effect=requests.exceptions.ConnectionError()))
    result = send_chatops_notification("test", Exception("err"))
    assert result is None


def test_does_not_raise_on_exception(monkeypatch):
    monkeypatch.setattr(requests, "post", MagicMock(side_effect=Exception("unexpected")))
    send_chatops_notification("test", Exception("err"))  # must not raise
