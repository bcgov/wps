import asyncio
import json
import datetime
import logging
import nats
from nats.aio.msg import Msg
from app.auto_spatial_advisory.nats import server, stream_name, hfi_classify_group, sfms_file_subject, subjects
from app.auto_spatial_advisory.process_hfi import RunType, process_hfi

logger = logging.getLogger(__name__)


def parse_nats_message(msg: Msg):
    """
    """
    if msg.subject == sfms_file_subject:
        decoded_msg = json.loads(json.loads(msg.data.decode()))
        run_type = RunType.from_str(decoded_msg['run_type'])
        run_date = datetime.datetime.strptime(decoded_msg['run_date'], "%Y-%m-%d").date()
        for_date = datetime.datetime.strptime(decoded_msg['for_date'], "%Y-%m-%d").date()
        return (run_type, run_date, for_date)


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

    async def cb(msg):
        run_type, run_date, for_date = parse_nats_message(msg)
        logger.info('Awaiting process_hfi({}, {}, {})\n'.format(run_type, run_date, for_date))
        await process_hfi(run_type, run_date, for_date)

    # idempotent operation, IFF stream with same configuration is added each time
    await jetstream.add_stream(name=stream_name, subjects=subjects)
    sfms_sub = await jetstream.subscribe(stream=stream_name,
                                         subject=sfms_file_subject,
                                         queue=hfi_classify_group,
                                         cb=cb)    # pylint: disable=invalid-name

    while True:
        msg = await sfms_sub.next_msg(timeout=None)
        logger.info('Msg received - {}\n'.format(msg))

if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    asyncio.run(run())
