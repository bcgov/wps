"""NATS consumer for smurfi.spot.update — sends email to spot forecast subscribers."""
import asyncio
import json
import logging

import nats
from nats.aio.msg import Msg
from nats.js.api import AckPolicy, ConsumerConfig, RetentionPolicy, StreamConfig
from wps_shared.db.crud.smurfi import get_active_subscribers_for_spot, get_spot_forecast_with_weather
from wps_shared.db.database import get_async_read_session_scope
from wps_shared.wps_logging import configure_logging

from app.smurfi.email import WEB_BASE_URL, build_spot_forecast_email, send_spot_forecast_emails
from app.smurfi.nats_config import (
    server,
    smurfi_spot_update_durable,
    smurfi_spot_update_subject,
    stream_name,
    subjects,
)

logger = logging.getLogger(__name__)


async def process_message(msg: Msg) -> None:
    try:
        decoded = json.loads(json.loads(msg.data.decode()))
        spot_request_id: int = decoded["spot_request_id"]
        spot_forecast_id: int = decoded["spot_forecast_id"]
        logger.info("Processing smurfi.spot.update for spot_request_id=%s", spot_request_id)

        async with get_async_read_session_scope() as session:
            subscribers = await get_active_subscribers_for_spot(session, spot_request_id)
            if not subscribers:
                logger.info("No active subscribers for spot_request_id=%s — skipping email", spot_request_id)
                await msg.ack()
                return
            spot_forecast = await get_spot_forecast_with_weather(session, spot_forecast_id)

        if spot_forecast is None:
            logger.error("SpotForecast %s not found — cannot send email", spot_forecast_id)
            await msg.nak(delay=60)
            return

        spot_detail_url = f"{WEB_BASE_URL}/smurfi/spots/{spot_request_id}"
        subject, html_body = build_spot_forecast_email(spot_forecast, spot_detail_url=spot_detail_url)
        emails = [s.email for s in subscribers]
        await send_spot_forecast_emails(subscriber_emails=emails, subject=subject, html_body=html_body)
        await msg.ack()
    except Exception as exc:
        logger.error("Error processing smurfi.spot.update: %s", msg.data, exc_info=exc)
        try:
            await msg.nak(delay=60)
        except Exception:
            logger.exception("Failed to nak message: %s", msg.data)


async def run() -> None:
    async def disconnected_cb():
        logger.info("Got disconnected!")

    async def reconnected_cb():
        logger.info("Got reconnected!")

    async def error_cb(error):
        logger.error("NATS error: %s", error)

    async def closed_cb():
        logger.info("Connection closed")

    nats_connection = await nats.connect(
        server,
        ping_interval=10,
        max_reconnect_attempts=24,
        disconnected_cb=disconnected_cb,
        reconnected_cb=reconnected_cb,
        error_cb=error_cb,
        closed_cb=closed_cb,
    )
    jetstream = nats_connection.jetstream()
    await jetstream.add_stream(
        name=stream_name,
        config=StreamConfig(retention=RetentionPolicy.WORK_QUEUE),
        subjects=subjects,
    )
    consumer_config = ConsumerConfig(
        durable_name=smurfi_spot_update_durable,
        ack_policy=AckPolicy.EXPLICIT,
        ack_wait=120,
        max_deliver=5,
    )
    sub = await jetstream.pull_subscribe(
        stream=stream_name,
        subject=smurfi_spot_update_subject,
        durable=smurfi_spot_update_durable,
        config=consumer_config,
    )
    logger.info("Smurfi NATS consumer started, listening on %s", smurfi_spot_update_subject)
    while True:
        msgs = await sub.fetch(batch=1, timeout=None)
        for msg in msgs:
            await process_message(msg)


if __name__ == "__main__":
    configure_logging()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    asyncio.run(run())
