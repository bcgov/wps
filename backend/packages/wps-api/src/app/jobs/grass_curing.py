import asyncio
import logging
import math
import os
import sys
import tempfile

import aiofiles
import numpy as np
from affine import Affine
from aiohttp import ClientSession
from osgeo import gdal, osr
from wps_shared.chatops_notification import send_chatops_notification
from wps_shared.db.crud.grass_curing import (
    get_last_percent_grass_curing_for_date,
    save_percent_grass_curing,
)
from wps_shared.db.database import get_async_read_session_scope, get_async_write_session_scope
from wps_shared.db.models.grass_curing import PercentGrassCuring
from wps_shared.geospatial.geospatial import SpatialReferenceSystem
from wps_shared.utils.time import get_utc_now
from wps_shared.wps_logging import configure_logging
from wps_wf1.wfwx_api import WfwxApi

logger = logging.getLogger(__name__)

GRASS_CURING_FILE_NAME_3978 = "grass_curing_epsg_3978.tif"
CWFIS_BASE_URL = "https://cwfis.cfs.nrcan.gc.ca/downloads/pcuring"


class GrassCuringFileNotFoundException(Exception):
    """Raised when the CWFIS grass curing file is not yet available for the requested date."""


class GrassCuringJob:
    """Job that downloads and processes percent grass curing data from the CWFIS."""

    def __init__(self):
        self.grass_cure_datetime = get_utc_now().replace(hour=0, minute=0, second=0, microsecond=0)

    async def _get_grass_curing_raster(self, path: str):
        """Gets the current percent grass curing as a tif from the CWFIS downloads endpoint."""
        filename = f"pc{self.grass_cure_datetime.strftime('%Y%m%d')}.tif"
        url = f"{CWFIS_BASE_URL}/{filename}"
        async with ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 404:
                    message = f"Grass curing file not yet available at {url}"
                    logger.warning(message)
                    raise GrassCuringFileNotFoundException(message)
                response.raise_for_status()
                content = await response.read()
        file_path = os.path.join(path, GRASS_CURING_FILE_NAME_3978)
        async with aiofiles.open(file_path, "wb") as file:
            await file.write(content)

    def _yield_value_for_stations(self, data_source, stations):
        """Given a list of stations, and a gdal dataset, yield the grass curing value for each station

        :param data_source: A gdal representation of a raster image of percent grass curing.
        :param stations: A list of weather station objects.
        :return: A tuple of a weather station code and the percent grass curing at its location.
        """
        raster_band = data_source.GetRasterBand(1)
        data_np_array = np.array(raster_band.ReadAsArray())
        forward_transform = Affine.from_gdal(*data_source.GetGeoTransform())
        reverse_transform = ~forward_transform

        source_srs = osr.SpatialReference()

        # station coords are in lat/lon aka WGS84/EPSG:4326 so we need a corresponding source srs
        # in order to perform the reprojection
        source_srs.ImportFromEPSG(SpatialReferenceSystem.WGS84.code)

        target_srs = osr.SpatialReference()
        target_srs.ImportFromWkt(data_source.GetProjection())

        # CoordinateTransformation.TransformPoint used below requires coords to be in lon, lat order
        # so we need to explicitly define the order
        source_srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
        target_srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)

        coord_transform = osr.CoordinateTransformation(source_srs, target_srs)

        rows, cols = data_np_array.shape
        for station in stations:
            x, y, _ = coord_transform.TransformPoint(station.long, station.lat)
            px, py = reverse_transform * (x, y)
            px = math.floor(px)
            py = math.floor(py)
            if px < 0 or py < 0 or px >= cols or py >= rows:
                logger.error(
                    "Station %s at pixel (%s, %s) is out of raster bounds, skipping",
                    station.code,
                    px,
                    py,
                )
                continue
            yield (station.code, data_np_array[py][px])

    async def _get_last_for_date(self):
        """Get the date of the most recently processed percent grass curing data."""
        async with get_async_read_session_scope() as session:
            result = await get_last_percent_grass_curing_for_date(session)
            return result

    async def _process_grass_curing(self):
        """Download and process percent grass curing data."""
        logger.info(
            f"Starting collection of percent grass curing data from CWFIS for {self.grass_cure_datetime}."
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            await self._get_grass_curing_raster(temp_dir)
            raster = gdal.Open(f"{temp_dir}/{GRASS_CURING_FILE_NAME_3978}")
            async with ClientSession() as http_session:
                wfwx_api = WfwxApi(http_session)
                stations = await wfwx_api.get_station_data()
            for station, value in self._yield_value_for_stations(raster, stations):
                percent_grass_curing = PercentGrassCuring(
                    for_date=self.grass_cure_datetime,
                    percent_grass_curing=value,
                    station_code=station,
                )
                async with get_async_write_session_scope() as session:
                    await save_percent_grass_curing(session, percent_grass_curing)
            raster = None
        logger.info(
            f"Finished processing percent grass curing data from CWFIS for {self.grass_cure_datetime}."
        )

    async def _run_grass_curing(self):
        """Entry point for running the job."""
        last_processed = await self._get_last_for_date()
        if last_processed is None or last_processed.date() < self.grass_cure_datetime.date():
            await self._process_grass_curing()
        else:
            logger.info(
                f"Percent grass curing processing is up to date as of {self.grass_cure_datetime}"
            )


def main():
    """Kicks off asynchronous processing of grass curing data."""
    try:
        # We don't want gdal to silently swallow errors.
        gdal.UseExceptions()
        logger.debug("Begin processing percent grass curing data.")

        bot = GrassCuringJob()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(bot._run_grass_curing())

        # Exit with 0 - success.
        sys.exit(os.EX_OK)
    except GrassCuringFileNotFoundException:
        # A missing file is expected early in the day. The job will re-try later.
        sys.exit(os.EX_OK)
    except Exception as exception:
        # Exit non 0 - failure.
        logger.error(
            "An error occurred while processing CWFIS grass curing data.", exc_info=exception
        )
        rc_message = ":scream: Encountered an error while processing CWFIS grass curing data."
        send_chatops_notification(rc_message, exception)
        sys.exit(os.EX_SOFTWARE)


if __name__ == "__main__":
    configure_logging()
    main()
