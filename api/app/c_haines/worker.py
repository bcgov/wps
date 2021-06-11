""" Entry point for generating c-haines charts from grib files.
"""
import logging
import asyncio
from app import configure_logging
from app.utils.s3 import get_client
from app.weather_models import ModelEnum, ProjectionEnum
from app.c_haines.severity_index import CHainesSeverityGenerator

logger = logging.getLogger(__name__)


async def main():
    """ Entry point for generating C-Haines severity index polygons. """
    async with get_client() as (client, bucket):
        models = (
            (ModelEnum.GDPS, ProjectionEnum.LATLON_15X_15),
            (ModelEnum.RDPS, ProjectionEnum.REGIONAL_PS),
            (ModelEnum.HRDPS, ProjectionEnum.HIGH_RES_CONTINENTAL),)
        for model, projection in models:
            logger.info('Generating C-Haines Severity Index for %s', model)
            generator = CHainesSeverityGenerator(model, projection, client, bucket)
            await generator.generate()


if __name__ == "__main__":
    configure_logging()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())
