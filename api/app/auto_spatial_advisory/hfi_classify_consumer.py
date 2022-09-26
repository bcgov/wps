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

    await js.subscribe(stream=stream_name,
                       subject="sfms.*",
                       queue=hfi_classify_group,
                       cb=cb)

if __name__ == '__main__':
    asyncio.run(main())
