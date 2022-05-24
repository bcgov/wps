"""
A script to list human fire starts datasets from object store to stdout.
"""
import asyncio
import os
import sys
import logging
import logging.config
from os.path import dirname, abspath
from app import configure_logging
from app.human_fire_starts.object_store import publish_datasets

logger = logging.getLogger(__name__)
DATASET_FOLDER_PATH = os.path.join(dirname(dirname(abspath(__file__))), 'data')


def main():
    """Walks data dir and passes each file path to publish to publish all files in data to object store"""
    try:
        dataset_paths = [os.path.join(DATASET_FOLDER_PATH, f) for f in os.listdir(DATASET_FOLDER_PATH)]
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(publish_datasets(dataset_paths))

        # Exit with 0 - success.
        logger.info('Successfully uploaded datasets')
        sys.exit(os.EX_OK)
    except Exception as exception:  # pylint: disable=broad-except
        # Exit non 0 - failure.
        logger.error('Failed to retrieve human fire starts datasets.',
                     exc_info=exception)
        sys.exit(os.EX_SOFTWARE)


if __name__ == '__main__':
    configure_logging()
    main()
