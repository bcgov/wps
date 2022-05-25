""" 
A script to list human fire starts datasets from object store to stdout.
"""
import asyncio
import os
import sys
import logging
import logging.config
from app import configure_logging
from app.human_fire_starts.object_store import download_latest_dataset

logger = logging.getLogger(__name__)


def main():
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(download_latest_dataset())

        # Exit with 0 - success.
        sys.exit(os.EX_OK)
    except Exception as exception:  # pylint: disable=broad-except
        # Exit non 0 - failure.
        logger.error('Failed to retrieve latest human fire starts dataset.',
                     exc_info=exception)
        sys.exit(os.EX_SOFTWARE)


if __name__ == '__main__':
    configure_logging()
    main()
