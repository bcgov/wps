""" Entry point for generating c-haines charts from grib files.
"""
import logging
from datetime import timedelta
from app.time_utils import get_utc_now
from app import configure_logging
from app.config import get
import app.db.database
from app.db.crud.c_haines import delete_older_than
from app.weather_models import ModelEnum, ProjectionEnum
from app.c_haines.severity_index import CHainesSeverityGenerator

logger = logging.getLogger(__name__)


def generate():
    """ Generate c-haines data """
    models = (
        (ModelEnum.GDPS, ProjectionEnum.LATLON_15X_15),
        (ModelEnum.RDPS, ProjectionEnum.REGIONAL_PS),
        (ModelEnum.HRDPS, ProjectionEnum.HIGH_RES_CONTINENTAL),)
    with app.db.database.get_write_session_scope() as session:
        for model, projection in models:
            logger.info('Generating C-Haines Severity Index for %s', model)
            generator = CHainesSeverityGenerator(model, projection, session)
            generator.generate()


def maintain():
    """ We don't have an infinite amount of storage, so we have to clean
    out the database. """
    max_age = int(get('MAX_AGE_C_HAINES', '26'))
    past = get_utc_now() - timedelta(weeks=max_age)
    with app.db.database.get_write_session_scope() as session:
        delete_older_than(session, past)


def main():
    """ Entry point for generating C-Haines severity index polygons. """
    try:
        generate()
    finally:
        maintain()


if __name__ == "__main__":
    configure_logging()
    main()
