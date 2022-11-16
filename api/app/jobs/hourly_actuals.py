""" Bot for loading hourly actual values.
"""
import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta
from aiohttp.client import ClientSession
from sqlalchemy.exc import IntegrityError
import db.database
import app.utils.time
from app import configure_logging
from db.crud.observations import save_hourly_actual
from app.rocketchat_notifications import send_rocketchat_notification
from app.wildfire_one import wfwx_api

logger = logging.getLogger(__name__)


class HourlyActualsJob():
    """ Job that downloads the hourly actuals from the wildfire website and stores it in a database. """

    def __init__(self):
        self.now = app.utils.time.get_pst_now()

    def _get_start_date(self) -> datetime:
        """ Return time N hour ago. E.g. if it's 17h15 now, we'd get YYYYMMDD16. The intention is that
        this bot runs every hour, so if we ask for everything from an hour back, we should be fine.
        However, just to be on the safe side, we're asking for the last three hours - just in case there
        was a station that came in late, or if for whatever reason we missed a run.
        """
        hour_ago = self.now - timedelta(hours=3)
        return hour_ago

    def _get_end_date(self) -> datetime:
        """ Return now. E.g. if it's 17h15 now, we'd get YYYYMMDD17 """
        return self.now

    async def run_wfwx(self):
        """ Entry point for running the bot """
        async with ClientSession() as session:
            header = await wfwx_api.get_auth_header(session)

            start_date = self._get_start_date()
            end_date = self._get_end_date()

            hourly_actuals = await wfwx_api.get_hourly_actuals_all_stations(
                session, header, start_date, end_date)

            logger.info('Retrieved %s hourly actuals', len(hourly_actuals))

        with db.database.get_write_session_scope() as session:
            for hourly_actual in hourly_actuals:
                try:
                    save_hourly_actual(session, hourly_actual)
                except IntegrityError:
                    logger.info('Skipping duplicate record for %s @ %s',
                                hourly_actual.station_code, hourly_actual.weather_date)
                    session.rollback()


def main():
    """ Makes the appropriate method calls in order to submit
    asynchronous queries to the Wildfire 1 API to get hourly values for all weather stations.
    """
    try:
        logger.debug('Retrieving hourly actuals...')
        bot = HourlyActualsJob()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(bot.run_wfwx())

        # Exit with 0 - success.
        sys.exit(os.EX_OK)
    except Exception as exception:  # pylint: disable=broad-except
        # Exit non 0 - failure.
        logger.error('Failed to retrieve hourly actuals.', exc_info=exception)
        rc_message = ':scream: Encountered error retrieving hourly actuals'
        send_rocketchat_notification(rc_message, exception)
        sys.exit(os.EX_SOFTWARE)


if __name__ == '__main__':
    configure_logging()
    main()
