"""Job that loads forecasters' noon forecasts from WF1 into the `wf1` and `by_time` tables in
object storage, as `FORECAST`."""

import asyncio
import logging
import os
import sys

import wps_shared.utils.time
from aiohttp.client import ClientSession
from wps_shared.chatops_notification import send_chatops_notification
from wps_shared.wps_logging import configure_logging
from wps_weather_data.by_time import ByTimeTable
from wps_weather_data.wf1 import Wf1Table, forecasts_table
from wps_wf1.wfwx_api import WfwxApi

logger = logging.getLogger(__name__)


class NoonForecastJob:
    """Implementation of class to process noon forecasts."""

    def __init__(self, wf1_table: Wf1Table | None = None, by_time_table: ByTimeTable | None = None):
        self.now = wps_shared.utils.time.get_utc_now()
        self.wf1_table = wf1_table or Wf1Table()
        self.by_time_table = by_time_table or ByTimeTable()

    async def run_wfwx(self):
        """Entry point for running the bot"""
        async with ClientSession() as session:
            wfwx_api = WfwxApi(session)
            noon_forecasts = await wfwx_api.get_noon_forecasts_all_stations(self.now)
            logger.info("Retrieved %s noon forecasts", len(noon_forecasts))

        rows = forecasts_table(noon_forecasts, wps_shared.utils.time.get_utc_now())
        # wf1 records each forecast as it changes, which WF1 itself does not keep. Every row is
        # merged into by_time, so a merge that failed after the append is made good next run.
        self.wf1_table.append_changed(rows)
        self.by_time_table.merge_wf1_rows(rows)


def main():
    """Makes the appropriate method calls in order to submit
    asynchronous queries to the Wildfire 1 API to get noon forecasts for all weather stations.
    """
    try:
        logger.debug("Retrieving noon forecasts...")
        bot = NoonForecastJob()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(bot.run_wfwx())

        # Exit with 0 - success.
        sys.exit(os.EX_OK)
    except Exception as exception:
        # Exit non 0 - failure.
        logger.error("Failed to retrieve noon forecasts.", exc_info=exception)
        rc_message = ":confounded: Encountered error retrieving noon forecasts"
        send_chatops_notification(rc_message, exception)
        sys.exit(os.EX_SOFTWARE)


if __name__ == "__main__":
    configure_logging()
    main()
