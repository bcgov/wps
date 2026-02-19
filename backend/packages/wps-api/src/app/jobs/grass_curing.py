from affine import Affine
from datetime import date
from aiohttp import ClientSession
from osgeo import gdal
import asyncio
import logging
import math
import numpy as np
import os
import requests
import sys
import tempfile
import xml.etree.ElementTree as ET

from wps_wf1.wfwx_api import WfwxApi
from wps_shared.wps_logging import configure_logging
from wps_shared.db.crud.grass_curing import get_last_percent_grass_curing_for_date, save_percent_grass_curing
from wps_shared.db.database import get_async_read_session_scope, get_async_write_session_scope
from wps_shared.geospatial.geospatial import WGS84
from wps_shared.db.models.grass_curing import PercentGrassCuring
from wps_shared.rocketchat_notifications import send_rocketchat_notification

logger = logging.getLogger(__name__)

GRASS_CURING_FILE_NAME_3978 = "grass_curing_epsg_3978.tif"
GRASS_CURING_FILE_NAME_4326 = "grass_curing_epsg_4326.tif"
GRASS_CURING_COVERAGE_ID = "public:pc_current"
WCS_URL = "https://cwfis.cfs.nrcan.gc.ca/geoserver/public/wcs"


class OwsException(Exception):
    """ Raise when OWS service returns an exception report."""


class GrassCuringJob():
    """ Job that downloads and processes percent grass curing data from the CWFIS. """

    async def _get_grass_curing_wcs_raster(self, path: str):
        """ Gets the current percent grass curing as a tif from the CWFIS Web Coverage Service. """
        session = requests.session()
        param_dict= {
            "service": "WCS",
            "version": "2.0.0",
            "request": "GetCoverage",
            "format": "image/geotiff",
            "coverageId": GRASS_CURING_COVERAGE_ID
        }
        response = session.get(WCS_URL, params = param_dict)
        # Check HTTP response code for error condition
        response.raise_for_status()
        # GeoServer can return an exception report as xml within a 200 response. Check if we have a content type header 
        # of application/xml and check if an exception is present.
        if "Content-Type" in response.headers and response.headers["Content-Type"] == "application/xml":
            root_element = ET.fromstring(response.content)
            if "ExceptionReport" in root_element.tag:
                message = f"GeoServer returned an exception when attempting to download percent grass curing from URL: {response.request.url}"
                logger.error(message)
                raise OwsException(message)
        file_path = os.path.join(path, GRASS_CURING_FILE_NAME_3978)
        with open(file_path, 'wb') as file:
            file.write(response.content)


    def _reproject_to_epsg_4326(self, path: str):
        """ Transforms coordinates in source_file geotiff to EPSG:3005 (BC Albers),
        writes to newly created geotiff called <new_filename>.tif

        :param path: A path to a temporary directory containing the percent grass curing tif.
        """
        destination_path = f"{path}/{GRASS_CURING_FILE_NAME_4326}"
        source_path = f"{path}/{GRASS_CURING_FILE_NAME_3978}"
        source_data = gdal.Open(source_path, gdal.GA_ReadOnly)
        gdal.Warp(destination_path, source_data, dstSRS=WGS84)
        del source_data

    
    def _yield_value_for_stations(self, data_source, stations):
        """ Given a list of stations, and a gdal dataset, yield the grass curing value for each station

        :param data_source: A gdal representation of a raster image of percent grass curing.
        :param stations: A list of weather station objects.
        :return: A tuple of a weather station code and the percent grass curing at its location.
        """
        raster_band = data_source.GetRasterBand(1)
        data_np_array = raster_band.ReadAsArray()
        data_np_array = np.array(data_np_array)
        forward_transform = Affine.from_gdal(*data_source.GetGeoTransform())
        reverse_transform = ~forward_transform
        for station in stations:
            longitude = station.long
            latitude = station.lat
            px, py = reverse_transform * (longitude, latitude)
            px = math.floor(px)
            py = math.floor(py)
            yield (station.code, data_np_array[py][px])


    async def _get_last_for_date(self):
        """ Get the date of the most recently processed percent grass curing data."""
        async with get_async_read_session_scope() as session:
            result =  await get_last_percent_grass_curing_for_date(session)
            return result


    async def _process_grass_curing(self):
        """ Download and process percent grass curing data. """
        async with get_async_write_session_scope() as session:
            today = date.today()
            logger.info(f"Starting collection of percent grass curing data from CWFIS for {today}.")
            with tempfile.TemporaryDirectory() as temp_dir:
                await self._get_grass_curing_wcs_raster(temp_dir)
                self._reproject_to_epsg_4326(temp_dir)

                # Open the reprojected grass curing data
                raster = gdal.Open(f"{temp_dir}/{GRASS_CURING_FILE_NAME_4326}")
                async with ClientSession() as http_session:
                    wfwx_api = WfwxApi(http_session)
                    stations = await wfwx_api.get_station_data()
                for station, value in self._yield_value_for_stations(raster, stations):
                    percent_grass_curing = PercentGrassCuring(for_date=today,
                                                                percent_grass_curing=value,
                                                                station_code=station )
                    await save_percent_grass_curing(session, percent_grass_curing)
        logger.info(f"Finished processing percent grass curing data from CWFIS for {today}.")
            

    async def _run_grass_curing(self):
        """ Entry point for running the job. """   
        last_processed = await self._get_last_for_date()
        if last_processed is None or last_processed.date() < date.today():
            await self._process_grass_curing()
        else:
            logger.info(f"Percent grass curing processing is up to date as of {date.today()}")


def main():
    """ Kicks off asynchronous processing of VIIRS snow coverage data.
    """
    try:
        # We don't want gdal to silently swallow errors.
        gdal.UseExceptions()
        logger.debug('Begin processing VIIRS snow coverage data.')

        bot = GrassCuringJob()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(bot._run_grass_curing())

        # Exit with 0 - success.
        sys.exit(os.EX_OK)
    except Exception as exception:
        # Exit non 0 - failure.
        logger.error("An error occurred while processing CWFIS grass curing data.", exc_info=exception)
        rc_message = ':scream: Encountered an error while processing CWFIS grass curing data.'
        send_rocketchat_notification(rc_message, exception)
        sys.exit(os.EX_SOFTWARE)

if __name__ == '__main__':
    configure_logging()
    main()