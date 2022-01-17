""" This is a job to pull noon forecasts from the Wildfire 1 API
for each weather station and store the results in our database.
"""
import asyncio
import os
import sys
import logging
import logging.config
from sqlalchemy.exc import IntegrityError
from aiohttp.client import ClientSession
from app import configure_logging
import app.db.database
from app.db.crud.forecasts import save_noon_forecast
from app.wildfire_one import wfwx_api
import app.utils.time
from app.rocketchat_notifications import send_rocketchat_notification

logger = logging.getLogger(__name__)


class NoonForecastJob():
    """ Implementation of class to process noon forecasts. """

    def __init__(self):
        self.now = app.utils.time.get_utc_now()

    async def run_wfwx(self):
        """ Entry point for running the bot """
        async with ClientSession() as session:
            header = await wfwx_api.get_auth_header(session)

            noon_forecasts = await wfwx_api.get_noon_forecasts_all_stations(
                session, header, self.now)
            logger.info('Retrieved %s noon forecasts', len(noon_forecasts))

        with app.db.database.get_write_session_scope() as session:
            for noon_forecast in noon_forecasts:
                try:
                    save_noon_forecast(session, noon_forecast)
                except IntegrityError as exception:
                    logger.info('Skipping duplicate record for %s @ %s',
                                noon_forecast.station_code, noon_forecast.weather_date, exc_info=exception)
                    session.rollback()


def main():
    """ Makes the appropriate method calls in order to submit
    asynchronous queries to the Wildfire 1 API to get noon forecasts for all weather stations.
    """
    try:
        logger.debug('Retrieving noon forecasts...')
        bot = NoonForecastJob()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(bot.run_wfwx())

        # Exit with 0 - success.
        sys.exit(os.EX_OK)
    except Exception as exception:  # pylint: disable=broad-except
        # Exit non 0 - failure.
        logger.error('Failed to retrieve noon forecasts.',
                     exc_info=exception)
        rc_message = ':confounded: Encountered error retrieving noon forecasts'
        send_rocketchat_notification(rc_message, exception)
        sys.exit(os.EX_SOFTWARE)


if __name__ == '__main__':
    configure_logging()
    main()
