"""
 Run the consumer processing logic locally
 Expects

    'OBJECT_STORE_SECRET'
    'OBJECT_STORE_USER_ID'
    'OBJECT_STORE_SERVER'

 to be set
"""
import sys
import asyncio
from datetime import date
from .. import common
from .. import process_cogs

if __name__ == '__main__':
    asyncio.run(process_cogs.process_cogs(common.RunType.ACTUAL, date.fromisoformat(
        sys.argv[1]), date.fromisoformat(sys.argv[2])))
