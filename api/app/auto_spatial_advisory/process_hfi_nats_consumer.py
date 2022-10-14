import asyncio
import json
import datetime
import logging
from nats.aio.msg import Msg
from app.auto_spatial_advisory.nats import server, stream_name, hfi_classify_group, sfms_file_subject, subjects
from app.auto_spatial_advisory.process_hfi import RunType, process_hfi
from app import configure_logging
from app.utils.add_nats_stream import NatsJetStream

logger = logging.getLogger(__name__)


def parse_nats_message(msg: Msg):
    """ Parse message from Nats message queue to extract necessary info needed for processing the file 
    in process_hfi().
    """
    if msg.subject == sfms_file_subject:
        decoded_msg = json.loads(json.loads(msg.data.decode()))
        run_type = RunType.from_str(decoded_msg['run_type'])
        run_date = datetime.datetime.strptime(decoded_msg['run_date'], "%Y-%m-%d").date()
        for_date = datetime.datetime.strptime(decoded_msg['for_date'], "%Y-%m-%d").date()
        return (run_type, run_date, for_date)


async def cb(msg):
    """ The callback function to be run whenever a message is received on the relevant queue with
    the sfms_file_subject. Will run process_hfi() for the specified run_type, run_date, and for_date.
    """
    run_type, run_date, for_date = parse_nats_message(msg)
    logger.info('Awaiting process_hfi({}, {}, {})\n'.format(run_type, run_date, for_date))
    await process_hfi(run_type, run_date, for_date)


async def create_and_subscribe():
    jetstream = NatsJetStream(server=server, stream_name=stream_name, subject=sfms_file_subject,
                              subjects=subjects, queue=hfi_classify_group, callback=cb)
    await jetstream.subscribe()


if __name__ == '__main__':
    configure_logging()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    asyncio.run(create_and_subscribe())
