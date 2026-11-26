"""Copy historical station observations from the BCWS data mart into object storage.

A way to run `wps_weather_data.data_mart_backfill` by path, which is what
scripts/run_against_pr_database.sh takes. See that module for what it does and its arguments.

    uv run python scripts/station_actuals_data_mart_backfill.py --from-year 1987
"""

import sys

from wps_weather_data.data_mart_backfill import main

if __name__ == "__main__":
    sys.exit(main())
