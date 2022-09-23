import asyncio
import logging
import nats
from app.auto_spatial_advisory.nats import server, stream_name, hfi_classify_group

logger = logging.getLogger(__name__)


async def main():
    nc = await nats.connect(server)
    js = nc.jetstream()

    async def cb(msg):
        logger.info('Classify HFI:', msg)

    async def disconnected_cb():
        logger.info('Got disconnected!')

    async def reconnected_cb():
        logger.info(f'Got reconnected to {nc.connected_url.netloc}')

    async def error_cb(e):
        logger.error(f'There was an error: {e}')

    async def closed_cb():
        logger.info('Connection is closed')

    # Queue Async Subscribe
    # NOTE: Here 'hfi_classify_group' becomes deliver_group, durable name and queue name.
    await js.subscribe(stream_name,
                       hfi_classify_group,
                       cb=cb,
                       error_cb=error_cb,
                       reconnected_cb=reconnected_cb,
                       disconnected_cb=disconnected_cb,
                       closed_cb=closed_cb)

if __name__ == '__main__':
    asyncio.run(main())
