"""
Nats consumer setup for consuming processing messages
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import List

import nats
from nats.aio.msg import Msg
from nats.js.api import AckPolicy, ConsumerConfig, RetentionPolicy, StreamConfig
from wps_shared import config
from wps_shared.utils.time import get_utc_datetime
from wps_shared.wps_logging import configure_logging

from app.auto_spatial_advisory.nats_config import (
    hfi_classify_durable_group,
    server,
    sfms_file_subject,
    stream_name,
    subjects,
)
from app.auto_spatial_advisory.process_hfi import RunType
from app.auto_spatial_advisory.process_stats import process_sfms_hfi_stats

logger = logging.getLogger(__name__)


def parse_nats_message(msg: Msg):
    """
    Parse the fields from the messages to drive the processing.

    :param msg: NATS message
    :return: A tuple of run_type, run_datetime, and for_date. for_date is in local Vancouver time.
    run_datetime is in utc time.
    """
    if msg.subject == sfms_file_subject:
        decoded_msg = json.loads(json.loads(msg.data.decode()))
        run_type = RunType.from_str(decoded_msg["run_type"])
        for_date = datetime.strptime(decoded_msg["for_date"], "%Y-%m-%d").date()
        # SFMS doesn't give us a timezone, but from the 2022 data it runs in local time
        # so we localize it as such then convert it to UTC
        run_datetime = get_utc_datetime(datetime.fromisoformat(decoded_msg["create_time"]))
        return (run_type, run_datetime, for_date)


async def process_message(msg: Msg):
    """Process a single JetStream message and only ack after successful processing."""
    try:
        logger.info("Msg received - %s\n", msg)
        run_type, run_datetime, for_date = parse_nats_message(msg)
        logger.info(
            "Awaiting process_sfms_hfi_stats({}, {}, {})\n".format(run_type, run_datetime, for_date)
        )
        await process_sfms_hfi_stats(run_type, run_datetime, for_date)
        await msg.ack()
    except Exception as exc:
        logger.error(
            "Error processing HFI message: %s, requesting JetStream redelivery",
            msg.data,
            exc_info=exc,
        )
        try:
            await msg.nak(delay=60)  # Request redelivery after 60 seconds
        except Exception:
            logger.exception("Failed to negatively acknowledge message: %s", msg.data)


async def run():
    async def disconnected_cb():
        logger.info("Got disconnected!")

    async def reconnected_cb():
        logger.info("Got reconnected!")

    async def error_cb(error):
        logger.error(f"There was an error: {error}")

    async def closed_cb():
        logger.info("Connection is closed")

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
    # we create a stream, this is important, we need to messages to stick around for a while!
    # idempotent operation, IFF stream with same configuration is added each time
    await jetstream.add_stream(
        name=stream_name,
        config=StreamConfig(retention=RetentionPolicy.WORK_QUEUE),
        subjects=subjects,
    )

    consumer_config = ConsumerConfig(
        durable_name=hfi_classify_durable_group,
        ack_policy=AckPolicy.EXPLICIT,
        ack_wait=300,  # 5 minutes
        max_deliver=6,  # initial try + 5 retries
    )

    sfms_sub = await jetstream.pull_subscribe(
        stream=stream_name,
        subject=sfms_file_subject,
        durable=hfi_classify_durable_group,
        config=consumer_config,
    )
    while True:
        msgs: List[Msg] = await sfms_sub.fetch(batch=1, timeout=None)
        for msg in msgs:
            await process_message(msg)


if __name__ == "__main__":
    configure_logging()
    creds_json = config.get("FCM_CREDS")
    if creds_json:
        from firebase_admin import credentials, initialize_app

        initialize_app(credentials.Certificate(json.loads(creds_json)))
    else:
        raise ValueError("FCM_CREDS is not set — Firebase cannot be initialized.")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    asyncio.run(run())
