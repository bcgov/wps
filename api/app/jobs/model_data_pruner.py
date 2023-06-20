""" A script that prunes old model data
"""
import os
import sys
import logging
from datetime import timedelta
from app.db.crud.weather_models import earliest_model_station_prediction, prune_model_station_predictions_between
from app.db.database import get_write_session_scope
from app.jobs.common_model_fetchers import (CompletedWithSomeExceptions)
from app import configure_logging
from app.rocketchat_notifications import send_rocketchat_notification
from app.utils.time import get_model_prune_range, get_utc_now

# If running as its own process, configure logging appropriately.
if __name__ == "__main__":
    configure_logging()

logger = logging.getLogger(__name__)


def main():
    try:
        with get_write_session_scope() as session:
            now = get_utc_now()
            start = earliest_model_station_prediction(session)[0]
            end = start + timedelta(days=14)
            range_start, range_end = get_model_prune_range(now, start, end)
            logger.info(f"Pruning model data from {range_start} to {range_end}")
            prune_model_station_predictions_between(session, start, end)
    except CompletedWithSomeExceptions:
        logger.warning('completed processing with some exceptions')
        sys.exit(os.EX_SOFTWARE)
    except Exception as exception:
        # We catch and log any exceptions we may have missed.
        logger.error('unexpected exception processing', exc_info=exception)
        rc_message = ':poop: Encountered error retrieving GFS model data from NOAA'
        send_rocketchat_notification(rc_message, exception)
        # Exit with a failure code.
        sys.exit(os.EX_SOFTWARE)
    # We assume success if we get to this point.
    sys.exit(os.EX_OK)


if __name__ == "__main__":
    main()
