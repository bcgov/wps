from datetime import date, timedelta
from osgeo import gdal
import asyncio
import glob
import logging
import os
import requests
import shutil
import sys
import tempfile
from app import config, configure_logging
from app.db.crud.snow import get_last_processed_snow_by_source, save_processed_snow
from app.db.database import get_async_read_session_scope, get_async_write_session_scope
from app.db.models.snow import ProcessedSnow, SnowSourceEnum
from app.rocketchat_notifications import send_rocketchat_notification
from app.utils.s3 import get_client

logger = logging.getLogger(__name__)

BC_BOUNDING_BOX = "-139.06,48.3,-114.03,60"
NSIDC_URL = "https://n5eil02u.ecs.nsidc.org/egi/request"
PRODUCT_VERSION = 2
SHORT_NAME = "VNP10A1F"
LAYER_VARIABLE = "/VIIRS_Grid_IMG_2D/CGF_NDSI_Snow_Cover"
RAW_SNOW_COVERAGE_NAME = 'raw_snow_coverage.tif'
RAW_SNOW_COVERAGE_CLIPPED_NAME = 'raw_snow_coverage_clipped.tif'


class ViirsSnowJob():
    """ Job that downloads and processed VIIRS snow coverage data from the NSIDC (https://nsidc.org).
    """

    async def _get_last_processed_date(self) -> date:
        """ Return the date of the most recent successful processing of VIIRS snow data.

        :return: The date of the most recent successful processing of VIIRS snow data.
        :rtype: date
        """
        async with get_async_read_session_scope() as session:
            last_processed = await get_last_processed_snow_by_source(session, SnowSourceEnum.viirs)
            return None if last_processed is None else last_processed[0].for_date.date()
    

    def _download_viirs_granules_by_date(self, for_date: date, path: str, file_name: str):
        """ Download VIIRS snow data for the specified date.
        
        :param for_date: The date of interest.
        :type for_date: date
        :param path: The path to a temporary directory to download the data to.
        :type path: str
        :param file_name: The name to assign to the downloaded file/archive.
        :type: file_name: str
        """
        # Interesting flow required by the NSIDC API. We need to issue a request without credentials which will fail
        # with a 401. The URL in the response object is the authentication endpoint, so we issue a request to it with basic auth.
        # Now we are authenticated with a session cookie and can make additional requests to the API.
        # Furthermore, it looks like we're stuck with synchronous requests.
        logger.info(f"Downloading VIIRS snow coverage data for date: {for_date.strftime('%Y-%m-%d')}")
        session = requests.session()
        resp = session.get(f"https://n5eil02u.ecs.nsidc.org/egi/capabilities/{SHORT_NAME}.{PRODUCT_VERSION}.xml")
        session.get(resp.url, auth=(config.get("NASA_EARTHDATA_USER"),config.get("NASA_EARTHDATA_PWD")))
        # Check if request was successful
        param_dict = {'short_name': SHORT_NAME, 
                        'version': PRODUCT_VERSION, 
                        'temporal': f"{for_date},{for_date}",
                        'bounding_box': BC_BOUNDING_BOX,
                        'bbox': BC_BOUNDING_BOX,
                        'format': "GeoTIFF", 
                        'projection': "GEOGRAPHIC", 
                        'Coverage': LAYER_VARIABLE, 
                        'page_size': 100, 
                        'request_mode': "stream"
                        }
        request = session.get(NSIDC_URL, params = param_dict)
        request.raise_for_status()
        file_path = os.path.join(path, file_name)
        with open(file_path, 'wb') as file:
            file.write(request.content)
        # unzip the snow coverage data
        shutil.unpack_archive(file_path, path)


    def _create_snow_coverage_mosaic(self, path: str):
        """ Use GDAL to create a mosaic from mulitple tifs of VIIRS snow data.

        :param path: The path to a temporary directory where the tifs are located. Also where the mosaic will be saved.
        :type path: str
        """
        output = os.path.join(path, RAW_SNOW_COVERAGE_NAME)
        files = glob.glob(os.path.join(path, "**/*.tif"), recursive=True)
        options = gdal.WarpOptions(format='GTiff', srcNodata=255)
        gdal.Warp(output, files, options=options)
        

    async def _clip_snow_coverage_mosaic(self, sub_dir: str, temp_dir: str):
        """ Clip the boundary of the snow data mosaic to the boundary of BC.

        :param sub_dir: The path to the location of the mosaic. Also the output path for the clipped image.
        :type sub_dir: str
        :param temp_dir: The path to the location of the geojson file used to clip the moasic.
        :type temp_dir: str
        """
        input_path = os.path.join(sub_dir, RAW_SNOW_COVERAGE_NAME)
        output_path = os.path.join(sub_dir, RAW_SNOW_COVERAGE_CLIPPED_NAME)
        cut_line_path = os.path.join(temp_dir, "bc_boundary.geojson")
        gdal.Warp(output_path, input_path, format='GTiff', cutlineDSName=cut_line_path)


    async def _get_bc_boundary_from_s3(self, path: str):
        """ Fetch the bc_boundary.geojson file from S3 and write a copy to the local temporary directory.
            The file will be used to clip the snow coverage mosaic to match the boundary of BC.

        :param path: The path to which to save the bc_boundary.geojson file.
        :type path: str
        """
        async with get_client() as (client, bucket):
            bc_boundary = await client.get_object(Bucket=bucket, Key="bc_boundary/bc_boundary.geojson")
            data = await bc_boundary['Body'].read()
            bc_boundary_geojson_path = os.path.join(path, "bc_boundary.geojson")
            with open(bc_boundary_geojson_path, "wb") as file:
                file.write(data)


    async def _save_clipped_snow_coverage_mosaic_to_s3(self, for_date: date, path: str):
        """ Save the clipped mosaic to S3 storage.

        :param for_date: The date of interest.
        :type for_date: date
        :param path: The path to the directory containing the mosaic.
        :type path: str  
        """
        async with get_client() as (client, bucket):
            key = f"snow_coverage/{for_date.strftime('%Y-%m-%d')}/clipped_snow_coverage_{for_date.strftime('%Y-%m-%d')}_epsg4326.tif"
            file_path = f"{path}/{RAW_SNOW_COVERAGE_CLIPPED_NAME}"
            with open(file_path, "rb") as file:
                await client.put_object(Bucket=bucket,
                                    Key=key,
                                    Body=file)


    async def _process_viirs_snow(self, for_date: date, path: str):
        """ Process VIIRS snow data.
        
        :param for_date: The date of interest.
        :type for_date: date
        :param path: A temporary file location for intermideiate files.
        :type path: str      
        """
        with tempfile.TemporaryDirectory() as sub_dir:
            file_name = f"{for_date.strftime('%Y-%m-%d')}.zip"
            self._download_viirs_granules_by_date(for_date, sub_dir, file_name)
            # Create a mosaic from the snow coverage imagery, clip it to the boundary of BC and save to S3
            self._create_snow_coverage_mosaic(sub_dir)
            await self._clip_snow_coverage_mosaic(sub_dir, path)
            await self._save_clipped_snow_coverage_moasic_to_s3(for_date, sub_dir)


    async def _run_viirs_snow(self):
        """ Entry point for running the job.
        """
        # Grab the date from our database of the last successful processing of VIIRS snow data.
        last_processed_date = await self._get_last_processed_date()
        today = date.today()
        if last_processed_date is None:
            # Case to cover the initial run of VIIRS snow processing (ie. start processing one week ago)
            next_date = today - timedelta(days=7)
        else:
            # Start processing the day after the last record of a successful job.
            next_date = last_processed_date + timedelta(days=1)
        if next_date >= today:
            logger.info("Processing of VIIRS snow data is up to date.")
            return
        with tempfile.TemporaryDirectory() as temp_dir:
            # Get the bc_boundary.geojson in a temp_dir. This is expensive so we only want to do this once.
            logger.info("Downloading bc_boundary.geojson from S3.")
            await self._get_bc_boundary_from_s3(temp_dir)
            while next_date < today:
                date_string = next_date.strftime('%Y-%m-%d')
                logger.info(f"Processing snow coverage data for date: {date_string}")
                try: 
                    await self._process_viirs_snow(next_date, temp_dir)
                    async with get_async_write_session_scope() as session:
                        processed_snow = ProcessedSnow(for_date=next_date, processed_date=today, snow_source=SnowSourceEnum.viirs)
                        await save_processed_snow(session, processed_snow)
                    logger.info(f"Successfully processed VIIRS snow coverage data for date: {date_string}")
                except requests.exceptions.HTTPError as http_error:
                    # An HTTPError with status code of 501 means the VIIRS imagery for the date in question is not yet
                    # available. Stop processing at the current date and exit the job. We'll try again later. This is 
                    # expected to occur and there is no need to send a notification to RocketChat.
                    if http_error.response.status_code == 501:
                        logger.info(f"VIIRS snow data is unavailable for date: {date_string}. Exiting job.")
                        break
                    else:
                        # If a different HTTPError occurred re-raise and let the next exception handler send a notification to RocketChat.
                        raise http_error
                next_date = next_date + timedelta(days=1)


def main():
    """ Kicks off asyncronous processing of VIIRS snow coverage data.
    """
    try:
        # We don't want gdal to silently swallow errors.
        gdal.UseExceptions()
        logger.debug('Begin processing VIIRS snow coverage data.')

        bot = ViirsSnowJob()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(bot._run_viirs_snow())

        # Exit with 0 - success.
        sys.exit(os.EX_OK)
    except Exception as exception:
        # Exit non 0 - failure.
        logger.error("An error occurred while processing VIIRS snow coverage data.", exc_info=exception)
        rc_message = ':scream: Encountered an error while processing VIIRS snow data.'
        send_rocketchat_notification(rc_message, exception)
        sys.exit(os.EX_SOFTWARE)

if __name__ == '__main__':
    configure_logging()
    main()