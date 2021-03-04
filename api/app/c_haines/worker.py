""" Entry point for generating c-haines charts from grib files.
"""
import logging

from app import configure_logging
import app.db.database
from app.weather_models import ModelEnum, ProjectionEnum

from app.c_haines.severity_index import CHainesSeverityGenerator

logger = logging.getLogger(__name__)


def main():
    """ Entry point for generating C-Haines severity index polygons. """
    models = (
        (ModelEnum.GDPS, ProjectionEnum.LATLON_15X_15),
        (ModelEnum.RDPS, ProjectionEnum.REGIONAL_PS),
        (ModelEnum.HRDPS, ProjectionEnum.HIGH_RES_CONTINENTAL),)
    with app.db.database.get_write_session_scope() as session:
        for model, projection in models:
            logger.info('Generating C-Haines Severity Index for %s', model)
            generator = CHainesSeverityGenerator(model, projection, session)
            generator.generate()


if __name__ == "__main__":
    configure_logging()
    main()
