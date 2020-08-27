""" Bot for loading hourly actual values.
"""

from datetime import timedelta
import logging
import sys
from requests import Session
from urllib.parse import urljoin
from app import configure_logging, config
from app.time_utils import get_pst_now
from app.fireweather_bot import BC_FIRE_WEATHER_BASE_URL, BC_FIRE_WEATHER_ENDPOINT, _authenticate_session

# If running as it's own process, configure logging appropriately.
if __name__ == "__main__":
    configure_logging()

logger = logging.getLogger(__name__)


class HourlyActualsBot():

    def __init__(self):
        self.now = get_pst_now()
        print('now is {}'.format(self.now))

    def get_start_date(self) -> int:
        """ Return time an hour ago. E.g. if it's 17h15 now, we'd get YYYYMMDD16"""
        hour_ago = self.now - timedelta(hours=1)
        return int(hour_ago.strftime('%Y%m%d%H'))

    def get_end_date(self) -> int:
        """ Return now. E.g. if it's 17h15 now, we'd get YYYYMMDD17 """
        return int(self.now.strftime('%Y%m%d%H'))

    def run(self):
        with Session() as session:
            _authenticate_session(session)
            # Submit the POST request to query hourlies for the station
            request_body = {
                'Start_Date': self.get_start_date(),
                'End_Date': self.get_end_date(),
                'Format': 'CSV',
                'cboFilters': config.get('BC_FIRE_WEATHER_FILTER_ID'),
                'rdoReport': 'OSBH',
            }
            url = urljoin(BC_FIRE_WEATHER_BASE_URL, BC_FIRE_WEATHER_ENDPOINT)
            response = session.post(url, data=request_body)
            print(response.text)


def main():
    """ Makes the appropriate method calls in order to submit a query to the BC FireWeather Phase 1 API
    to get hourly values for all weather stations, downloads the resulting CSV file, writes
    the CSV file to the database, then deletes the local copy of the CSV file.
    """
    logger.debug('Retrieving hourly actuals...')
    bot = HourlyActualsBot()
    bot.run()
    # Exit with 0 - success.
    sys.exit(0)


if __name__ == '__main__':
    main()
