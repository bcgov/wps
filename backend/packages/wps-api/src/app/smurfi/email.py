import html
import logging

import httpx
from wps_shared import config
from wps_shared.utils.time import vancouver_tz

logger = logging.getLogger(__name__)

CHES_TOKEN_URL = config.get("CHES_TOKEN_URL")
CHES_CLIENT_ID = config.get("CHES_CLIENT_ID")
CHES_CLIENT_SECRET = config.get("CHES_CLIENT_SECRET")
CHES_SENDER_EMAIL = config.get("CHES_SENDER_EMAIL")
CHES_EMAIL_MERGE_URL = "https://ches.api.gov.bc.ca/api/v1/email/merge"
WEB_BASE_URL = config.get("WEB_BASE_URL")


def build_spot_forecast_email(spot_forecast, spot_detail_url: str) -> tuple[str, str]:
    """Return (subject, html_body) for a spot forecast notification email."""
    sr = spot_forecast.spot_request
    fire_numbers = html.escape(", ".join(sr.fire_number)) if sr.fire_number else "N/A"
    subject = f"Spot Forecast Update: Fire {fire_numbers}"

    descriptive_rows = ""
    for dw in spot_forecast.descriptive_weather:
        descriptive_rows += (
            f"<tr><td>{html.escape(str(dw.period))}</td><td>{html.escape(dw.conditions or '')}</td>"
            f"<td>{dw.temperature}°C</td><td>{dw.relative_humidity}%</td></tr>"
        )

    tabular_rows = ""
    for tw in spot_forecast.tabular_weather:
        time_str = tw.forecast_time.astimezone(vancouver_tz).strftime("%Y-%m-%d %H:%M %Z") if tw.forecast_time else ""
        tabular_rows += (
            f"<tr><td>{time_str}</td><td>{tw.temperature}°C</td>"
            f"<td>{tw.relative_humidity}%</td><td>{html.escape(tw.wind or '')}</td>"
            f"<td>{tw.probability_of_precipitation}%</td><td>{tw.precipitation_amount} mm</td></tr>"
        )

    html_body = f"""
<html><body>
<h2>Spot Forecast Update</h2>
<p><strong>Fire Number(s):</strong> {fire_numbers}</p>
<p><strong>Location:</strong> {html.escape(sr.geographic_description or '')}</p>

<h3>Descriptive Forecast</h3>
<table border="1" cellpadding="4" cellspacing="0">
  <thead><tr><th>Period</th><th>Conditions</th><th>Temperature</th><th>RH</th></tr></thead>
  <tbody>{descriptive_rows}</tbody>
</table>

<h3>Tabular Forecast</h3>
<table border="1" cellpadding="4" cellspacing="0">
  <thead><tr><th>Time</th><th>Temp</th><th>RH</th><th>Wind</th><th>PoP</th><th>Precip</th></tr></thead>
  <tbody>{tabular_rows}</tbody>
</table>

<p><a href="{html.escape(spot_detail_url)}">View Spot Forecast</a></p>
</body></html>
"""
    return subject, html_body


async def send_spot_forecast_emails(subscriber_emails: list[str], subject: str, html_body: str) -> None:
    """Fetch a CHES OAuth2 token and send bulk email via /email/merge."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            token_response = await client.post(
                CHES_TOKEN_URL,
                data={
                    "grant_type": "client_credentials",
                    "client_id": CHES_CLIENT_ID,
                    "client_secret": CHES_CLIENT_SECRET,
                },
            )
            token_response.raise_for_status()
            token_data = token_response.json()
            access_token = token_data.get("access_token")
            if not access_token:
                raise ValueError(f"CHES token response missing access_token: {token_data}")

            merge_payload = {
                "subject": subject,
                "from": CHES_SENDER_EMAIL,
                "bodyType": "html",
                "body": html_body,
                "contexts": [{"to": [email], "context": {}} for email in subscriber_emails],
            }

            merge_response = await client.post(
                CHES_EMAIL_MERGE_URL,
                json=merge_payload,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            merge_response.raise_for_status()
            logger.info("Sent spot forecast email to %d subscriber(s)", len(subscriber_emails))
    except Exception:
        logger.exception(
            "Failed to send spot forecast email to %d subscriber(s) (subject: %s)",
            len(subscriber_emails),
            subject,
        )
        raise
