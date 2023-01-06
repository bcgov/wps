"""
Nats consumer setup for consuming processing messages
"""
# pylint: skip-file
import asyncio
import json
import datetime
from datetime import datetime
import logging
from typing import List
from starlette.background import BackgroundTasks
import nats
from nats.js.api import StreamConfig, RetentionPolicy
from nats.aio.msg import Msg
from app.auto_spatial_advisory.nats_config import server, stream_name, sfms_file_subject, subjects, hfi_classify_durable_group
from app.auto_spatial_advisory.process_hfi import RunType, process_hfi, process_hfi_with_snow_coverage
from app.nats_publish import publish
from app import configure_logging
from app.utils.time import get_utc_datetime

logger = logging.getLogger(__name__)


def parse_nats_message(msg: Msg):
    """
     Parse the fields from the messages to drive the processing
    """
    if msg.subject == sfms_file_subject:
        decoded_msg = json.loads(json.loads(msg.data.decode()))
        run_type = RunType.from_str(decoded_msg['run_type'])
        run_date = datetime.strptime(decoded_msg['run_date'], "%Y-%m-%d").date()
        for_date = datetime.strptime(decoded_msg['for_date'], "%Y-%m-%d").date()

        # SFMS doesn't give us a timezone, but from the 2022 data it runs in local time
        # so we localize it as such then convert it to UTC
        run_datetime = get_utc_datetime(datetime.fromisoformat(decoded_msg['create_time']))
        return (run_type, run_date, run_datetime, for_date)


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
    await jetstream.add_stream(name=stream_name,
                               config=StreamConfig(retention=RetentionPolicy.WORK_QUEUE),
                               subjects=subjects)
    sfms_sub = await jetstream.pull_subscribe(stream=stream_name,
                                              subject=sfms_file_subject,
                                              durable=hfi_classify_durable_group)
    while True:
        msgs: List[Msg] = await sfms_sub.fetch(batch=1, timeout=None)
        for msg in msgs:
            try:
                logger.info('Msg received - {}\n'.format(msg))
                await msg.ack()
                run_type, run_date, run_datetime, for_date = parse_nats_message(msg)
                logger.info('Awaiting process_hfi({}, {}, {})\n'.format(run_type, run_date, for_date))
                # await process_hfi(RunType.FORECAST, for_date, for_date, for_date)
                await process_hfi_with_snow_coverage(run_type, for_date, for_date, for_date)
            except Exception as e:
                logger.error("Error processing HFI message: %s, adding back to queue", msg.data, exc_info=e)
                background_tasks = BackgroundTasks()
                background_tasks.add_task(publish, stream_name, sfms_file_subject, msg, subjects)


if __name__ == '__main__':
    configure_logging()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    asyncio.run(run())
