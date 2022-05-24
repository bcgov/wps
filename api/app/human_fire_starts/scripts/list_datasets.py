""" 
A script to list human fire starts datasets from object store to stdout.
"""
import asyncio
import os
import sys
import logging
import logging.config
from app import configure_logging
from app.human_fire_starts.object_store import list_datasets

logger = logging.getLogger(__name__)


def main():
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(list_datasets())

        # Exit with 0 - success.
        sys.exit(os.EX_OK)
    except Exception as exception:  # pylint: disable=broad-except
        # Exit non 0 - failure.
        logger.error('Failed to retrieve human fire starts datasets.',
                     exc_info=exception)
        sys.exit(os.EX_SOFTWARE)


if __name__ == '__main__':
    configure_logging()
    main()
