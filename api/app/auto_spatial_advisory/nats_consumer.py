import asyncio
import nats
from app.auto_spatial_advisory.nats import server, stream_name, hfi_classify_group


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
        print(msg)

    sfms_sub = await js.subscribe(stream="wps-pr-2261sfms",
                                  subject="sfms.*",
                                  queue=hfi_classify_group,
                                  cb=cb)

    while True:
        msg = await sfms_sub.next_msg(timeout=None)
        print(msg)

if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    asyncio.run(run())
