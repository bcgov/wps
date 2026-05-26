import html
import logging
from datetime import date

import httpx
from wps_shared import config
from wps_shared.utils.time import vancouver_tz

logger = logging.getLogger(__name__)

CHES_TOKEN_URL = config.get("CHES_TOKEN_URL")
CHES_CLIENT_ID = config.get("CHES_CLIENT_ID")
CHES_CLIENT_SECRET = config.get("CHES_CLIENT_SECRET")
CHES_SENDER_EMAIL = config.get("CHES_SENDER_EMAIL")
CHES_EMAIL_MERGE_URL = config.get("CHES_MERGE_URL")
WEB_BASE_URL = config.get("WEB_BASE_URL")

_TABLE_STYLE = "border-collapse:collapse;width:100%;font-size:12px;"
_CELL_STYLE = "border:1px solid black;padding:3px 8px;"
_HDR_STYLE = f"{_CELL_STYLE}font-weight:bold;"
_NUM_STYLE = f"{_CELL_STYLE}font-weight:bold;text-align:center;"
_DASH_STYLE = f"{_CELL_STYLE}text-align:center;"


def _to_ddm(decimal: float) -> str:
    abs_val = abs(decimal)
    degrees = int(abs_val)
    minutes = (abs_val - degrees) * 60
    sign = "-" if decimal < 0 else ""
    return f"{sign}{degrees} {minutes:.3f}"


def _get_coords(spot_request) -> str:
    try:
        from geoalchemy2.shape import to_shape
        from wps_shared.geospatial.geospatial import (
            NAD83_BC_ALBERS,
            PointTransformer,
            SpatialReferenceSystem,
        )

        shape = to_shape(spot_request.geom)
        lat, lon = PointTransformer(
            NAD83_BC_ALBERS, SpatialReferenceSystem.WGS84.code
        ).transform_coordinate(shape.x, shape.y)
        return f"{_to_ddm(lat)},{_to_ddm(lon)}"
    except Exception:
        return "—"


def _format_date_label(forecast_time, issued_at) -> str:
    ft = forecast_time.astimezone(vancouver_tz)
    issued_day: date = issued_at.astimezone(vancouver_tz).date()
    day_diff = (ft.date() - issued_day).days
    time_str = ft.strftime("%H%M")

    if day_diff == 0:
        return f"Today {time_str}"
    if day_diff == 1:
        return "Tonight" if ft.hour == 0 else f"Tomorrow {time_str}"
    if day_diff == 2:
        return "Tomorrow night" if ft.hour == 0 else f"Next Day {time_str}"
    return ft.strftime("%Y-%m-%d %H%M")


def _ensure_period(text: str | None) -> str:
    if not text:
        return ""
    return text if text.endswith(".") else f"{text}."


def build_spot_forecast_email(spot_forecast, spot_detail_url: str) -> tuple[str, str]:
    """Return (subject, html_body) for a spot forecast notification email."""
    sr = spot_forecast.spot_request_base
    instance = spot_forecast.spot_request_instance
    fire_numbers = html.escape(", ".join(sr.fire_number)) if sr.fire_number else "N/A"
    subject = f"Spot Forecast Update: Fire {fire_numbers}"

    issued_dt = spot_forecast.issued_at.astimezone(vancouver_tz)
    issued_str = (
        issued_dt.strftime("%H%M")
        + " "
        + issued_dt.strftime("%Z")
        + " "
        + issued_dt.strftime("%A, %B %-d, %Y")
    )

    expiry_dt = (
        spot_forecast.expires_at.astimezone(vancouver_tz) if spot_forecast.expires_at else None
    )
    expiry_str = expiry_dt.strftime("%A %B %-d") if expiry_dt else "—"

    coords_str = _get_coords(sr)
    aspect_str = html.escape(sr.aspect or "—")
    elevation_str = f"{sr.elevation} m" if sr.elevation else "—"
    geo_str = html.escape(sr.geographic_description or "")
    forecaster_name = html.escape(spot_forecast.forecaster_name or "")
    forecaster_email = html.escape(spot_forecast.forecaster_email or "")
    forecaster_phone = html.escape(spot_forecast.forecaster_phone or "—")
    requestor_name = html.escape(sr.requestor_name or "")
    fire_size_str = (
        f"Size:&nbsp;&nbsp;&nbsp;{spot_forecast.fire_size} ha" if spot_forecast.fire_size else ""
    )

    station_codes = spot_forecast.representative_station_codes
    stations_str = ", ".join(str(c) for c in station_codes) if station_codes else "—"

    # Descriptive weather
    dw_by_period = {dw.period: dw for dw in spot_forecast.descriptive_weather}
    forecast_lines = ""
    afternoon = dw_by_period.get("Today")
    tonight = dw_by_period.get("Tonight")
    tomorrow = dw_by_period.get("Tomorrow")

    if afternoon:
        cond = html.escape(_ensure_period(afternoon.conditions))
        forecast_lines += (
            f"<p style='margin:2px 0;font-size:12px;'><strong>AFTERNOON:</strong>&nbsp;&nbsp;"
            f"{cond} MAX TEMP {afternoon.temperature}C, MIN RH {afternoon.relative_humidity}%</p>"
        )
    if tonight:
        cond = html.escape(_ensure_period(tonight.conditions))
        forecast_lines += (
            f"<p style='margin:2px 0;font-size:12px;'><strong>TONIGHT:</strong>&nbsp;&nbsp;"
            f"{cond} MIN TEMP {tonight.temperature}C. MAX RH {tonight.relative_humidity}%.</p>"
        )
    if tomorrow:
        cond = html.escape(_ensure_period(tomorrow.conditions))
        forecast_lines += (
            f"<p style='margin:2px 0;font-size:12px;'><strong>TOMORROW:</strong>&nbsp;&nbsp;"
            f"{cond} TEMP {tomorrow.temperature}C. MIN RH {tomorrow.relative_humidity}%.</p>"
        )

    # Tabular weather
    sorted_tabular = sorted(spot_forecast.tabular_weather, key=lambda tw: tw.forecast_time)
    tabular_rows = ""
    for tw in sorted_tabular:
        label = (
            _format_date_label(tw.forecast_time, spot_forecast.issued_at)
            if tw.forecast_time
            else ""
        )
        tabular_rows += (
            f"<tr>"
            f"<td style='{_CELL_STYLE}'>{html.escape(label)}</td>"
            f"<td style='{_NUM_STYLE}'>{tw.temperature if tw.temperature is not None else '-'}</td>"
            f"<td style='{_NUM_STYLE}'>{tw.relative_humidity if tw.relative_humidity is not None else '-'}</td>"
            f"<td style='{_NUM_STYLE}'>{html.escape(tw.wind or '-')}</td>"
            f"<td style='{_DASH_STYLE}'>{tw.precipitation_amount if tw.precipitation_amount is not None else '-'}</td>"
            f"<td style='{_DASH_STYLE}'>{tw.probability_of_precipitation if tw.probability_of_precipitation is not None else '-'}</td>"
            f"</tr>"
        )

    synopsis = html.escape(spot_forecast.synopsis or "")
    inversion = html.escape(spot_forecast.inversion_and_venting or "")
    outlook = html.escape(spot_forecast.outlook or "")
    confidence = html.escape(spot_forecast.confidence or "")

    outlook_block = (
        f"<p style='font-size:12px;line-height:1.6;'>"
        f"<strong><span style='text-decoration:underline;'>OUTLOOK (3-5 Day Outlook)</span></strong> {outlook}</p>"
        if outlook
        else ""
    )

    html_body = f"""
<html><body style="font-family:Arial,sans-serif;max-width:800px;margin:0 auto;padding:16px;">

<h2 style="font-weight:bold;text-decoration:underline;text-align:center;font-size:18px;">
  BC Wild Fire Service Spot Forecast
</h2>

<div style="display:flex;justify-content:space-between;margin-bottom:4px;font-size:12px;">
  <span><strong><span style="text-decoration:underline;">Date/time Issued:</span></strong>&nbsp;&nbsp;{issued_str}</span>
  <span><strong><span style="text-decoration:underline;">Default Expiry:</span></strong> {expiry_str}</span>
</div>

<table style="{_TABLE_STYLE}">
  <tr>
    <td style="{_HDR_STYLE}width:145px;">Fire/Proj #</td>
    <td style="{_CELL_STYLE}width:210px;">{fire_numbers}</td>
    <td style="{_CELL_STYLE}" colspan="2">Request by:&nbsp;&nbsp;{requestor_name}</td>
  </tr>
  <tr>
    <td style="{_CELL_STYLE}">Forecast by</td>
    <td style="{_CELL_STYLE}">{forecaster_name}</td>
    <td style="{_CELL_STYLE}">Email: {forecaster_email}</td>
    <td style="{_CELL_STYLE}">Phone: {forecaster_phone}</td>
  </tr>
  <tr>
    <td style="{_CELL_STYLE}">Geographic</td>
    <td style="{_CELL_STYLE}">{geo_str}</td>
    <td style="{_CELL_STYLE}" colspan="2">Representative <span style="text-decoration:underline;">Stations</span>: {stations_str}</td>
  </tr>
  <tr>
    <td style="{_CELL_STYLE}">Coordinates (<span style="text-decoration:underline;">approx</span>)</td>
    <td style="{_CELL_STYLE}">{coords_str}</td>
    <td style="{_CELL_STYLE}">Slope/aspect:&nbsp;&nbsp;{aspect_str}</td>
    <td style="{_CELL_STYLE}"></td>
  </tr>
  <tr>
    <td style="{_CELL_STYLE}">Elevation</td>
    <td style="{_CELL_STYLE}">{elevation_str}</td>
    <td style="{_CELL_STYLE}">{fire_size_str}</td>
    <td style="{_CELL_STYLE}"></td>
  </tr>
</table>

<p style="font-size:12px;line-height:1.6;">
  <strong><span style="text-decoration:underline;">SYNOPSIS:</span></strong>&nbsp;&nbsp;{synopsis}
</p>

<div style="margin-top:6px;">
  <p style="margin:2px 0;font-size:12px;"><strong><span style="text-decoration:underline;">FORECAST:</span></strong></p>
  {forecast_lines}
</div>

<table style="{_TABLE_STYLE}margin-top:12px;">
  <tr>
    <th style="{_HDR_STYLE}text-align:left;">Date/Time (PDT)</th>
    <th style="{_HDR_STYLE}text-align:center;">Temp (C)</th>
    <th style="{_HDR_STYLE}text-align:center;">RH</th>
    <th style="{_HDR_STYLE}text-align:center;">Wind (km/h)</th>
    <th style="{_HDR_STYLE}text-align:center;">Rain (mm)</th>
    <th style="{_HDR_STYLE}text-align:center;">Chance Rain</th>
  </tr>
  {tabular_rows}
</table>

<p style="font-size:12px;line-height:1.6;">
  <strong><span style="text-decoration:underline;">INVERSION &amp; VENTING:</span></strong>&nbsp;&nbsp;&nbsp;&nbsp;{inversion}
</p>

{outlook_block}

<p style="font-size:12px;line-height:1.6;">
  <strong><span style="text-decoration:underline;">CONFIDENCE/DISCUSSION:</span></strong>&nbsp;&nbsp;{confidence}
</p>

<p><a href="{html.escape(spot_detail_url)}">View Spot Forecast</a></p>
</body></html>
"""
    return subject, html_body


async def send_spot_forecast_emails(
    subscriber_emails: list[str], subject: str, html_body: str
) -> None:
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
