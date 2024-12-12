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
from datetime import date, datetime
from app import configure_logging


from app.auto_spatial_advisory.run_type import RunType
from .. import process_stats

if __name__ == "__main__":
    configure_logging()
    run_datetime = datetime.fromisoformat(sys.argv[1])
    run_date = run_datetime.date()
    for_date = date.fromisoformat(sys.argv[2])
    asyncio.run(process_stats.process_stats(RunType.FORECAST, run_datetime, run_date, for_date))
