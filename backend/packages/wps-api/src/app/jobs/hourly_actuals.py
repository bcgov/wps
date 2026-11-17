"""Job that loads hourly observations from WF1 into the `wf1` and `by_time` tables in object
storage, as `ACTUALS`, and writes the daily observation to `by_time`."""

import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta

import wps_shared.utils.time
from aiohttp.client import ClientSession
from wps_shared.chatops_notification import send_chatops_notification
from wps_shared.wps_logging import configure_logging
from wps_weather_data.by_time import ByTimeTable
from wps_weather_data.wf1 import Wf1Table, actuals_table, merge_daily_actuals
from wps_wf1.wfwx_api import WfwxApi

logger = logging.getLogger(__name__)


class HourlyActualsJob:
    """Job that downloads the hourly actuals from WF1 and stores them in object storage."""

    def __init__(self, wf1_table: Wf1Table | None = None, by_time_table: ByTimeTable | None = None):
        self.now = wps_shared.utils.time.get_pst_now()
        self.wf1_table = wf1_table or Wf1Table()
        self.by_time_table = by_time_table or ByTimeTable()

    def _get_start_date(self) -> datetime:
        """Return time N hour ago. E.g. if it's 17h15 now, we'd get YYYYMMDD16. The intention is that
        this bot runs every hour, so if we ask for everything from an hour back, we should be fine.
        However, just to be on the safe side, we're asking for the last three hours - just in case there
        was a station that came in late, or if for whatever reason we missed a run.
        """
        hour_ago = self.now - timedelta(hours=3)
        return hour_ago

    def _get_end_date(self) -> datetime:
        """Return now. E.g. if it's 17h15 now, we'd get YYYYMMDD17"""
        return self.now

    async def run_wfwx(self):
        """Entry point for running the bot"""

        start_date = self._get_start_date()
        end_date = self._get_end_date()
        async with ClientSession() as session:
            wfwx_api = WfwxApi(session)
            hourly_actuals = await wfwx_api.get_hourly_actuals_all_stations(start_date, end_date)

            logger.info("Retrieved %s hourly actuals", len(hourly_actuals))

        rows = actuals_table(hourly_actuals, wps_shared.utils.time.get_utc_now())
        # wf1 records what changed. Every row is merged into by_time, so a merge that failed after
        # the append is made good by the next run, which fetches the same hours again.
        self.wf1_table.append_changed(rows)
        self.by_time_table.merge_wf1_rows(rows)
        # The daily observation is the 20:00 UTC one, with the precip of the 24 hours before it.
        merge_daily_actuals(self.by_time_table, rows)


def main():
    """Makes the appropriate method calls in order to submit
    asynchronous queries to the Wildfire 1 API to get hourly values for all weather stations.
    """
    try:
        logger.debug("Retrieving hourly actuals...")
        bot = HourlyActualsJob()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(bot.run_wfwx())

        # Exit with 0 - success.
        sys.exit(os.EX_OK)
    except Exception as exception:
        # Exit non 0 - failure.
        logger.error("Failed to retrieve hourly actuals.", exc_info=exception)
        rc_message = ":scream: Encountered error retrieving hourly actuals"
        send_chatops_notification(rc_message, exception)
        sys.exit(os.EX_SOFTWARE)


if __name__ == "__main__":
    configure_logging()
    main()
