import asyncio
import nats
from app.auto_spatial_advisory.nats import server, stream_name, hfi_classify_group


async def main():
    nc = await nats.connect(server)
    js = nc.jetstream()

    async def cb(msg):
        print('Classify HFI:', msg)

    # Queue Async Subscribe
    # NOTE: Here 'hfi_classify_group' becomes deliver_group, durable name and queue name.
    await js.subscribe(stream_name, hfi_classify_group, cb=cb)

if __name__ == '__main__':
    asyncio.run(main())
