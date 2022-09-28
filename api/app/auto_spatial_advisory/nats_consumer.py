import asyncio
import json
import datetime
import nats
from app.auto_spatial_advisory.nats import server, stream_name, hfi_classify_group, sfms_file_subject, subjects
from app.auto_spatial_advisory.process_hfi import RunType, process_hfi


def parse_nats_message(msg):
    """
    """
    if msg.subject == 'sfms.file':
        json_data = json.loads(json.loads(msg.data))
        run_type = RunType.from_str(json_data['run_type'])
        run_date = datetime.datetime.strptime(json_data['run_date'], "%Y-%m-%d").date()
        for_date = datetime.datetime.strptime(json_data['for_date'], "%Y-%m-%d").date()
        return (run_type, run_date, for_date)
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
        run_type, run_date, for_date = parse_nats_message(msg)
        print('Awaiting process_hfi({}, {}, {})\n'.format(run_type, run_date, for_date))
        await process_hfi(run_type, run_date, for_date)

    # idempotent operation, IFF stream with same configuration is added each time
    await js.add_stream(name=stream_name, subjects=subjects)
    sfms_sub = await js.subscribe(stream=stream_name,
                                  subject=sfms_file_subject,
                                  queue=hfi_classify_group,
                                  cb=cb)

    while True:
        msg = await sfms_sub.next_msg(timeout=None)
        print('Msg received - {}\n'.format(msg))

if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    asyncio.run(run())
