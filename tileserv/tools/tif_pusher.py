import sys
import asyncio
import os
import logging
from datetime import date
from typing import List
from decouple import config

from s3 import get_client

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)


def get_filenames(tif_dir) -> List[str]:
    filenames: List[str] = os.listdir(tif_dir)
    lower_filenames: List[str] = list(map(lambda x: x.lower(), filenames))
    tif_filenames: List[str] = list(filter(lambda f: f.endswith('tif') or f.endswith('tiff'), lower_filenames))
    hfi_tif_filenames: List[str] = list(filter(lambda f: os.path.basename(f).startswith('hfi'), tif_filenames))
    return hfi_tif_filenames


async def main(issue_date: date, for_date: date, tif_dir):
    logger.info('Generating SFMS uploads for issue date: "%s" for_date: "%s"',
                issue_date.isoformat(), for_date.isoformat())
    config('OBJECT_STORE_SECRET')
    config('OBJECT_STORE_USER_ID')
    config('OBJECT_STORE_SERVER')
    config('OBJECT_STORE_BUCKET')

    async with get_client() as (client, bucket):
        # We save the Last-modified and Create-time as metadata in the object store - just
        # in case we need to know about it in the future.
        logger.info('Client is %s', client.meta.endpoint_url)
        client.

    # Iterate over all files in the directory
    # for filename in get_filenames(tif_dir):
    #     filename = os.path.join(tif_dir, filename)
    #     try:
    #         # TODO upload logic
    #         logger.info(filename)
    #     except KeyboardInterrupt:
    #         logger.warning('Aborted')
    #         sys.exit(1)
    #     except Exception as exception:
    #         logger.error('Error uploading "%s" with %s', filename, exception, exc_info=True)
    #         print(sys.exc_info()[0])


if __name__ == '__main__':
    if len(sys.argv) != 4:
        print('Usage: python3 tif_pusher.py issue_date for_date tif_dir')
        sys.exit(1)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main(date.fromisoformat(sys.argv[1]), date.fromisoformat(sys.argv[2]), sys.argv[3]))
    # main(date.fromisoformat(sys.argv[1]), date.fromisoformat(sys.argv[2]), sys.argv[3])
