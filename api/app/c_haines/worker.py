""" Entry point for generating c-haines charts from grib files.
"""
import logging
from app import configure_logging
from app.weather_models import ModelEnum, ProjectionEnum
from app.c_haines.severity_index import CHainesSeverityGenerator

logger = logging.getLogger(__name__)


def main():
    """ Entry point for generating C-Haines severity index polygons. """
    """ Generate c-haines data """
    models = (
        (ModelEnum.GDPS, ProjectionEnum.LATLON_15X_15),
        (ModelEnum.RDPS, ProjectionEnum.REGIONAL_PS),
        (ModelEnum.HRDPS, ProjectionEnum.HIGH_RES_CONTINENTAL),)
    for model, projection in models:
        logger.info('Generating C-Haines Severity Index for %s', model)
        generator = CHainesSeverityGenerator(model, projection)
        generator.generate()


if __name__ == "__main__":
    configure_logging()
    main()
