import asyncio
import json
import nats
from nats.aio.client import Client as NATS
from app.auto_spatial_advisory.nats import server, stream_name, hfi_classify_group


def parse_nats_message(msg):
    """
    """
    if msg.subject == 'sfms.file':
        json_data = json.loads(json.loads(msg.data))
        print(json_data)
        run_type = json_data['run_type']
        key = json_data['key']
        run_date = json_data['run_date']
        for_date = json_data['for_date']
        print('Run type: {}; Key: {}; Run date: {}; For date: {}\n'.format(run_type, key, run_date, for_date))
    else:
        return


async def run():
    async def disconnected_cb():
        print("Got disconnected!")

    async def reconnected_cb():
        print("Got reconnected!")

    async def error_cb(e):
        print(f"There was an error: {e}")

    async def closed_cb():
        print("Connection is closed")

    nc = await nats.connect(
        server,
        ping_interval=10,
        max_reconnect_attempts=24,
        disconnected_cb=disconnected_cb,
        reconnected_cb=reconnected_cb,
        error_cb=error_cb,
        closed_cb=closed_cb,
    )
    js = nc.jetstream()

    async def cb(msg):
        parse_nats_message(msg)

    sfms_sub = await js.subscribe(stream=stream_name,
                                  subject="sfms.*",
                                  queue=hfi_classify_group,
                                  cb=cb)

    while True:
        msg = await sfms_sub.next_msg(timeout=None)
        print('Msg received - {}\n'.format(msg))

if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    asyncio.run(run())
