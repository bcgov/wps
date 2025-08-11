"""
Run the consumer processing logic locally
Expects

   'OBJECT_STORE_SECRET'
   'OBJECT_STORE_USER_ID'
   'OBJECT_STORE_SERVER'

to be set
----------------------

If you're trying to reprocess stats that have already been run, you can ensure all stats get
re-calculated by deleting the original records from the database (excluding the run_parameters table)

DO $$
DECLARE run_ids INT[];  -- Declare an array variable to store the list of run_id's
BEGIN
    -- Populate the array dynamically from a query using a date range
    SELECT array_agg(id) INTO run_ids
    FROM run_parameters
    WHERE for_date BETWEEN '2024-10-23' AND '2024-10-25';

    -- Delete from all tables using the run_ids array
    DELETE FROM advisory_fuel_stats WHERE run_parameters = ANY(run_ids);
    DELETE FROM advisory_tpi_stats WHERE run_parameters = ANY(run_ids);
    DELETE FROM advisory_elevation_stats WHERE run_parameters = ANY(run_ids);
    DELETE FROM high_hfi_area WHERE run_parameters = ANY(run_ids);
    DELETE FROM advisory_hfi_wind_speed WHERE run_parameters = ANY(run_ids);
    DELETE FROM advisory_hfi_percent_conifer WHERE run_parameters = ANY(run_ids);
    DELETE FROM critical_hours WHERE run_parameters = ANY(run_ids);

END $$;
"""

import sys
import asyncio
from datetime import date, timedelta
from wps_shared.db.crud.auto_spatial_advisory import get_most_recent_run_parameters
from wps_shared.db.database import get_async_read_session_scope
from wps_shared.wps_logging import configure_logging
from wps_shared.run_type import RunType
from .. import process_stats


async def main(for_dates: list[date], run_type: RunType):
    async with get_async_read_session_scope() as session:
        for for_date in for_dates:
            # try to reprocess the run that ASA will look for
            run_param = await get_most_recent_run_parameters(session, run_type, for_date)
            if run_param:
                run_datetime = run_param[0].run_datetime
                await process_stats.process_sfms_hfi_stats(run_type, run_datetime, for_date)
            else:
                print(f"No run params found for {for_date} - {run_type.value}")


if __name__ == "__main__":
    configure_logging()

    start_date = date.fromisoformat(sys.argv[1])
    end_date = date.fromisoformat(sys.argv[2])
    run_type = RunType.from_str(sys.argv[3])

    date_range = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]

    asyncio.run(main(date_range, run_type))
