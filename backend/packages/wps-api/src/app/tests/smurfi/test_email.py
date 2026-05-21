"""Unit tests for smurfi CHES email builder."""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.smurfi.email import build_spot_forecast_email, send_spot_forecast_emails


def _make_spot_request(fire_number=None, geographic_description="Test Area"):
    sr = MagicMock()
    sr.fire_number = fire_number or ["V0800168"]
    sr.geographic_description = geographic_description
    return sr


def _make_spot_forecast(spot_request, descriptive_weather=None, tabular_weather=None):
    sf = MagicMock()
    sf.spot_request = spot_request
    sf.descriptive_weather = descriptive_weather or []
    sf.tabular_weather = tabular_weather or []
    return sf


def _make_descriptive(period, conditions="Sunny", temperature=18.0, relative_humidity=40.0):
    dw = MagicMock()
    dw.period = period
    dw.conditions = conditions
    dw.temperature = temperature
    dw.relative_humidity = relative_humidity
    return dw


def _make_tabular(forecast_time, temperature=18.0, relative_humidity=40.0, wind="NW 20", probability_of_precipitation=10.0, precipitation_amount=0.0):
    tw = MagicMock()
    tw.forecast_time = forecast_time
    tw.temperature = temperature
    tw.relative_humidity = relative_humidity
    tw.wind = wind
    tw.probability_of_precipitation = probability_of_precipitation
    tw.precipitation_amount = precipitation_amount
    return tw


def test_build_email_subject_includes_fire_number():
    """Email subject contains the fire number."""
    sr = _make_spot_request(fire_number=["V0800168"])
    sf = _make_spot_forecast(sr)
    subject, _ = build_spot_forecast_email(sf, spot_detail_url="http://example.com/smurfi/spots/1")
    assert "V0800168" in subject


def test_build_email_body_contains_geographic_description():
    """Email body contains the geographic description."""
    sr = _make_spot_request(geographic_description="Clearwater Valley")
    sf = _make_spot_forecast(sr)
    _, html = build_spot_forecast_email(sf, spot_detail_url="http://example.com/smurfi/spots/1")
    assert "Clearwater Valley" in html


def test_build_email_body_contains_descriptive_period():
    """Email body contains descriptive weather period."""
    sr = _make_spot_request()
    dw = _make_descriptive(period="Today", conditions="Partly cloudy", temperature=22.0, relative_humidity=35.0)
    sf = _make_spot_forecast(sr, descriptive_weather=[dw])
    _, html = build_spot_forecast_email(sf, spot_detail_url="http://example.com/smurfi/spots/1")
    assert "Today" in html
    assert "Partly cloudy" in html


def test_build_email_body_contains_tabular_row():
    """Email body contains a tabular weather row."""
    sr = _make_spot_request()
    tw = _make_tabular(
        forecast_time=datetime(2026, 5, 19, 14, 0, tzinfo=timezone.utc),
        temperature=21.0,
        relative_humidity=38.0,
        wind="SE 15",
    )
    sf = _make_spot_forecast(sr, tabular_weather=[tw])
    _, html = build_spot_forecast_email(sf, spot_detail_url="http://example.com/smurfi/spots/1")
    assert "SE 15" in html


def test_build_email_body_contains_spot_detail_link():
    """Email body contains the view-forecast link."""
    sr = _make_spot_request()
    sf = _make_spot_forecast(sr)
    _, html = build_spot_forecast_email(sf, spot_detail_url="http://example.com/smurfi/spots/99")
    assert "http://example.com/smurfi/spots/99" in html


@pytest.mark.anyio
async def test_send_spot_forecast_emails_calls_ches():
    """send_spot_forecast_emails fetches a token and POSTs to CHES /email/merge."""
    mock_token_response = MagicMock()
    mock_token_response.json.return_value = {"access_token": "test-token"}
    mock_token_response.raise_for_status = MagicMock()

    mock_merge_response = MagicMock()
    mock_merge_response.raise_for_status = MagicMock()

    with patch("app.smurfi.email.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client
        mock_client.post.side_effect = [mock_token_response, mock_merge_response]

        await send_spot_forecast_emails(
            subscriber_emails=["a@example.com", "b@example.com"],
            subject="Test Subject",
            html_body="<p>Test</p>",
        )

        assert mock_client.post.call_count == 2
        merge_call = mock_client.post.call_args_list[1]
        merge_body = merge_call.kwargs.get("json") or merge_call.args[1]
        assert len(merge_body["contexts"]) == 2
        assert merge_body["contexts"][0]["to"] == ["a@example.com"]
        assert merge_body["contexts"][1]["to"] == ["b@example.com"]
