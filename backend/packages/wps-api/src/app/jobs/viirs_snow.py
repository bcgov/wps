import argparse
import asyncio
import glob
import logging
import os
import re
import sys
import tempfile
from datetime import date, datetime, timedelta

import aiofiles
import earthaccess as ea
import numpy as np
from osgeo import gdal, osr
from wps_shared.db.crud.snow import get_last_processed_snow_by_processed_date, save_processed_snow
from wps_shared.db.database import get_async_read_session_scope, get_async_write_session_scope
from wps_shared.db.models.snow import ProcessedSnow, SnowSourceEnum
from wps_shared.geospatial.geospatial import SpatialReferenceSystem
from wps_shared.rocketchat_notifications import send_rocketchat_notification
from wps_shared.utils.polygonize import polygonize_in_memory
from wps_shared.utils.s3 import get_client
from wps_shared.utils.time import vancouver_tz
from wps_shared.wps_logging import configure_logging

from app.utils.pmtiles import tippecanoe_wrapper, write_geojson

logger = logging.getLogger(__name__)

PRODUCT_VERSION = 2
SHORT_NAME = "VNP10A1F"
RAW_SNOW_COVERAGE_NAME = "raw_snow_coverage.tif"
RAW_SNOW_COVERAGE_CLIPPED_NAME = "raw_snow_coverage_clipped.tif"
BINARY_SNOW_COVERAGE_CLASSIFICATION_NAME = "binary_snow_coverage.tif"
SNOW_COVERAGE_PMTILES_MIN_ZOOM = 4
SNOW_COVERAGE_PMTILES_MAX_ZOOM = 11
SNOW_COVERAGE_PMTILES_PERMISSIONS = "public-read"
VARIABLE = "CGF_NDSI_Snow_Cover"
DST_NODATA = 255
BBOX = (-139.06, 48.3, -114.03, 60.0)
COMPRESS = "LZW"
R_SPHERE = 6371007.181  # meters
TILE_SIZE_M = 1111950.519  # meters (tile width/height)
GLOBAL_ULX = -20015109.354
GLOBAL_ULY = 10007554.677
MODIS_SINUSOIDAL_PROJ4 = "+proj=sinu +R=6371007.181 +nadgrids=@null +wktext +units=m +no_defs"
RESAMPLING = "near"
SUBDATASET = "://HDFEOS/GRIDS/VIIRS_Grid_IMG_2D/Data_Fields/CGF_NDSI_Snow_Cover"

class NoGranulesException(Exception):
    """
    Raise No Granules Exception when no snow data available for a date

    """

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


def get_pmtiles_filepath(for_date: date, filename: str) -> str:
    """
    Returns the S3 storage key for storing the snow coverage pmtiles for the given date and file name.


    :param for_date: The date of snow coverage imagery.
    :type run_date: date
    :param filename: snowCoverage[for_date].pmtiles -> snowCoverage20230821.pmtiles
    :type filename: str
    :return: s3 bucket key for pmtiles file
    :rtype: str
    """
    pmtiles_filepath = os.path.join(
        "psu", "pmtiles", "snow", for_date.strftime("%Y-%m-%d"), filename
    )

    return pmtiles_filepath


class ViirsSnowJob:
    """Job that downloads and processed VIIRS snow coverage data from the NSIDC (https://nsidc.org)."""

    async def _get_last_processed_date(self, for_date: datetime) -> date:
        """Return the date of the most recent successful processing of VIIRS snow data.

        :return: The date of the most recent successful processing of VIIRS snow data.
        :rtype: date
        """
        async with get_async_read_session_scope() as session:
            last_processed = await get_last_processed_snow_by_processed_date(
                session, for_date, SnowSourceEnum.viirs
            )
            return None if last_processed is None else last_processed[0].for_date.date()

    def _download_viirs_granules_by_date(self, for_date: date, path: str):
        """
        Download VIIRS snow data for the specified date using the NSIDC earthaccess package.

        :param for_date: The date of interest.
        :type for_date: date
        :param path: The path to a temporary directory to download the data to.
        :type path: str
        :param file_name: The name to assign to the downloaded file/archive.
        :type: file_name: str
        """
        auth = ea.login(strategy="environment")
        assert auth.authenticated, "Earthdata Login failed; set EARTHDATA_USERNAME/PASSWORD."

        granules = ea.search_data(
            short_name=SHORT_NAME,
            version=PRODUCT_VERSION,
            temporal=(f"{for_date}", f"{for_date}"),
            bounding_box=BBOX,
            count=500,
        )
        if not granules:
            raise NoGranulesException(f"No granules found for {for_date}. Exiting snow processing.")

        # ---------- download ----------
        downloaded = ea.download(granules, path)
        print(f"Downloaded {len(downloaded)} HDF5 tiles to {path}")
        h5_paths = [path for path in downloaded if path.name.endswith("h5")]
        return h5_paths

    def _create_snow_coverage_mosaic(self, path: str):
        """Use GDAL to create a mosaic from mulitple tifs of VIIRS snow data.

        :param path: The path to a temporary directory where the tifs are located. Also where the mosaic will be saved.
        :type path: str
        """
        output = os.path.join(path, RAW_SNOW_COVERAGE_NAME)
        files = glob.glob(os.path.join(path, "**/*.tif"), recursive=True)
        options = gdal.WarpOptions(format="GTiff", srcNodata=255)
        gdal.Warp(output, files, options=options)

    async def _clip_snow_coverage_mosaic(self, sub_dir: str, temp_dir: str):
        """Clip the boundary of the snow data mosaic to the boundary of BC.

        :param sub_dir: The path to the location of the mosaic. Also the output path for the clipped image.
        :type sub_dir: str
        :param temp_dir: The path to the location of the geojson file used to clip the mosaic.
        :type temp_dir: str
        """
        input_path = os.path.join(sub_dir, RAW_SNOW_COVERAGE_NAME)
        output_path = os.path.join(sub_dir, RAW_SNOW_COVERAGE_CLIPPED_NAME)
        cut_line_path = os.path.join(temp_dir, "bc_boundary.geojson")
        gdal.Warp(
            output_path, input_path, format="GTiff", cutlineDSName=cut_line_path, cropToCutline=True
        )

    async def _get_bc_boundary_from_s3(self, path: str):
        """Fetch the bc_boundary.geojson file from S3 and write a copy to the local temporary directory.
            The file will be used to clip the snow coverage mosaic to match the boundary of BC.

        :param path: The path to which to save the bc_boundary.geojson file.
        :type path: str
        """
        async with get_client() as (client, bucket):
            bc_boundary = await client.get_object(
                Bucket=bucket, Key="bc_boundary/bc_boundary.geojson"
            )
            data = await bc_boundary["Body"].read()
            bc_boundary_geojson_path = os.path.join(path, "bc_boundary.geojson")
            with open(bc_boundary_geojson_path, "wb") as file:
                file.write(data)

    async def _save_clipped_snow_coverage_mosaic_to_s3(self, for_date: date, path: str):
        """Save the clipped mosaic to S3 storage.

        :param for_date: The date of interest.
        :type for_date: date
        :param path: The path to the directory containing the mosaic.
        :type path: str
        """
        async with get_client() as (client, bucket):
            key = f"snow_coverage/{for_date.strftime('%Y-%m-%d')}/clipped_snow_coverage_{for_date.strftime('%Y-%m-%d')}_epsg4326.tif"
            file_path = f"{path}/{RAW_SNOW_COVERAGE_CLIPPED_NAME}"
            with open(file_path, "rb") as file:
                await client.put_object(Bucket=bucket, Key=key, Body=file)

    def _classify_snow_coverage(self, path: str):
        source_path = os.path.join(path, RAW_SNOW_COVERAGE_CLIPPED_NAME)
        source = gdal.Open(source_path, gdal.GA_ReadOnly)
        source_band = source.GetRasterBand(1)
        source_data = source_band.ReadAsArray()
        # Classify the data. Snow coverage in the source data is indicated by values in the range of 0-100. I'm using a range of
        # 10 - 100 to increase confidence. In the classified data 1 is assigned to snow covered pixels and all other pixels are 0.
        classified = np.where((source_data > 10) & (source_data <= 100), 1, 0)
        output_driver = gdal.GetDriverByName("GTiff")
        classified_snow_path = os.path.join(path, BINARY_SNOW_COVERAGE_CLASSIFICATION_NAME)
        classified_snow = output_driver.Create(
            classified_snow_path,
            xsize=source_band.XSize,
            ysize=source_band.YSize,
            bands=1,
            eType=gdal.GDT_Byte,
        )
        classified_snow.SetGeoTransform(source.GetGeoTransform())
        classified_snow.SetProjection(source.GetProjection())
        classified_snow_band = classified_snow.GetRasterBand(1)
        classified_snow_band.WriteArray(classified)
        source_data = None
        source_band = None
        source = None
        classified_snow_band = None
        classified_snow = None

    async def _create_pmtiles_layer(self, path: str, for_date: date):
        filename = os.path.join(path, BINARY_SNOW_COVERAGE_CLASSIFICATION_NAME)
        with polygonize_in_memory(filename, "snow", "snow") as layer:
            # We need a geojson file to pass to tippecanoe
            temp_geojson = write_geojson(layer, path)
            pmtiles_filename = f"snowCoverage{for_date.strftime('%Y%m%d')}.pmtiles"
            temp_pmtiles_filepath = os.path.join(path, pmtiles_filename)
            logger.info(f"Writing snow coverage pmtiles -- {pmtiles_filename}")
            tippecanoe_wrapper(
                temp_geojson,
                temp_pmtiles_filepath,
                min_zoom=SNOW_COVERAGE_PMTILES_MIN_ZOOM,
                max_zoom=SNOW_COVERAGE_PMTILES_MAX_ZOOM,
            )

            async with (
                get_client() as (client, bucket),
                aiofiles.open(temp_pmtiles_filepath, "rb") as f,
            ):
                key = get_pmtiles_filepath(for_date, pmtiles_filename)
                logger.info(f"Uploading snow coverage file {pmtiles_filename} to {key}")
                contents = await f.read()
                await client.put_object(
                    Bucket=bucket,
                    Key=key,
                    ACL=SNOW_COVERAGE_PMTILES_PERMISSIONS,  # We need these to be accessible to everyone
                    Body=contents,
                )
            logger.info("Done uploading snow coverage file")

    def _build_modis_sinu_wkt(self) -> str:
        srs = osr.SpatialReference()
        srs.ImportFromProj4(MODIS_SINUSOIDAL_PROJ4)
        return srs.ExportToWkt()

    def _compute_bounds_for_tile(self, h: int, v: int, width: int, height: int):
        """
        Compute ULX/ULY/LRX/LRY in meters for a MODIS Sinusoidal tile and raster size.
        Pixel size is derived from tile size / pixels (more accurate than nominal resolution).
        """
        px = TILE_SIZE_M / float(width)
        py = TILE_SIZE_M / float(height)
        # Compute upper-left tile corner in meters
        ulx = GLOBAL_ULX + h * TILE_SIZE_M
        uly = GLOBAL_ULY - v * TILE_SIZE_M
        # Lower-right
        lrx = ulx + width * px
        lry = uly - height * py
        return ulx, uly, lrx, lry, px, py

    def _read_tile_indices(self, meta: dict, src_name: str):
        """
        Try to infer (h, v) from metadata or filename pattern h##v##.
        """
        h = None
        v = None
        # From metadata (HDF-EOS5 commonly provides these)
        for key in ["HorizontalTileNumber", "HORIZONTALTILENUMBER"]:
            if key in meta:
                try:
                    h = int(meta[key])
                    break
                except Exception:
                    pass
        for key in ["VerticalTileNumber", "VERTICALTILENUMBER"]:
            if key in meta:
                try:
                    v = int(meta[key])
                    break
                except Exception:
                    pass

        # From filename (hXXvYY)
        if h is None or v is None:
            m = re.search(r"h(\d{2})v(\d{2})", src_name)
            if m:
                h = int(m.group(1))
                v = int(m.group(2))

        if h is None or v is None:
            raise RuntimeError("Could not determine tile indices (h,v) from metadata or filename.")
        return h, v

    def _translate_assign_sinu(
        self,
        src_name: str,
        dst_tif: str,
        ulx: float,
        uly: float,
        lrx: float,
        lry: float,
        sinu_wkt: str,
    ):
        opts = gdal.TranslateOptions(
            format="GTiff", outputSRS=sinu_wkt, outputBounds=[ulx, uly, lrx, lry]
        )
        out = gdal.Translate(dst_tif, src_name, options=opts)
        if out is None:
            raise RuntimeError("gdal.Translate failed when assigning sinusoidal georeference.")
        out.FlushCache()
        out = None

    def _warp_to_wgs84(self, src_name_or_ds, dst_tif: str, resampling: str, dstnodata: float):
        warp_options = gdal.WarpOptions(
            dstSRS=SpatialReferenceSystem.WGS84.epsg,
            resampleAlg=resampling,
            format="GTiff",
            dstNodata=dstnodata,
        )
        out = gdal.Warp(dst_tif, src_name_or_ds, options=warp_options)
        if out is None:
            raise RuntimeError("gdal.Warp failed.")
        out.FlushCache()
        out = None

    def _convert_h5_to_geotiff(self, temp_dir: str, h5_path: str):
        ds = gdal.Open(h5_path)
        if ds is None:
            raise RuntimeError(f"Cannot open subdataset: {h5_path}")
        # Attempt to derive NoData from band 1 if not specified
        dstnodata = DST_NODATA
        b1 = ds.GetRasterBand(1)
        if b1 is not None:
            nd = b1.GetNoDataValue()
            if nd is not None:
                dstnodata = nd
        meta = ds.GetMetadata()
        h, v = self._read_tile_indices(meta, h5_path)
        width, height = ds.RasterXSize, ds.RasterYSize
        ulx, uly, lrx, lry, px, py = self._compute_bounds_for_tile(h, v, width, height)

        print("Assigning MODIS Sinusoidal georeference with:")
        print(f"  h={h}, v={v}, size={width}x{height}, px={px:.6f} m, py={py:.6f} m")
        print(f"  ULX={ulx:.3f}, ULY={uly:.3f}, LRX={lrx:.3f}, LRY={lry:.3f}")

        sinu_name = f"sinu_{h}_{v}.tif"
        sinu_path = os.path.join(temp_dir, sinu_name)
        sinu_wkt = self._build_modis_sinu_wkt()
        self._translate_assign_sinu(ds, sinu_path, ulx, uly, lrx, lry, sinu_wkt)

        wgs84_name = f"wgs_84_{h}_{v}.tif"
        wgs84_path = os.path.join(temp_dir, wgs84_name)
        self._warp_to_wgs84(sinu_path, wgs84_path, RESAMPLING, dstnodata)
        os.remove(sinu_path)  # Remove the intermediate tif with the sinusoidal projection
        ds = None

    async def _process_viirs_snow(self, for_date: date, path: str):
        """Process VIIRS snow data.

        :param for_date: The date of interest.
        :type for_date: date
        :param path: A temporary file location for intermediate files.
        :type path: str
        """
        with tempfile.TemporaryDirectory() as sub_dir:
            h5_paths = self._download_viirs_granules_by_date(for_date, sub_dir)
            # The downloaded snow data is in a HDF5 format (.h5 file extension). Convert to WGS84 geotiffs.
            for h5_path in h5_paths:
                subdataset_path = f'HDF5:"{h5_path}"{SUBDATASET}'
                self._convert_h5_to_geotiff(sub_dir, subdataset_path)
            # Create a mosaic from the snow coverage imagery, clip it to the boundary of BC and save to S3
            self._create_snow_coverage_mosaic(sub_dir)
            await self._clip_snow_coverage_mosaic(sub_dir, path)
            await self._save_clipped_snow_coverage_mosaic_to_s3(for_date, sub_dir)
            # Reclassify the clipped snow coverage mosaic to 1 for snow and 0 for all other cells
            self._classify_snow_coverage(sub_dir)
            # Create pmtiles file and save to S3
            await self._create_pmtiles_layer(sub_dir, for_date)

    async def _run_viirs_snow_default(self):
        """Logic for determining start and end dates for processing snow coverage data via a cronjob."""
        end_datetime = datetime.now(tz=vancouver_tz)

        # Grab the date from our database of the last successful processing of VIIRS snow data.
        last_processed_date = await self._get_last_processed_date(end_datetime)
        end_date = end_datetime.date()
        if last_processed_date is None:
            # Case to cover the initial run of VIIRS snow processing (ie. start processing yesterday)
            start_date = end_date - timedelta(days=1)
        elif end_date - last_processed_date > timedelta(days=14):
            # Jan 13, 2025 - Start gathering snow data from two weeks ago
            start_date = end_date - timedelta(days=14)
        else:
            # Start processing the day after the last record of a successful job.
            start_date = last_processed_date + timedelta(days=1)
        if start_date >= end_date:
            logger.info("Processing of VIIRS snow data is up to date.")
            return
        await self._run_viirs_snow_by_date(start_date, end_date)

    async def _run_viirs_snow_with_args(self, args: argparse.Namespace):
        """Logic for processing snow coverage data for a start and end date provided as command line arguments."""
        start_datetime = datetime.fromisoformat(args.start_datetime)
        end_datetime = datetime.fromisoformat(args.end_datetime)
        if start_datetime is None:
            logger.warning(" The start_arg is required to process viirs snow with arguments.")
            return
        if end_datetime is None:
            logger.warning(" The end_arg is required to process viirs snow with arguments.")
            return
        await self._run_viirs_snow_by_date(start_datetime.date(), end_datetime.date())

    async def _run_viirs_snow_by_date(self, next_date: date, end_date: date):
        """Process snow coverage data from next_date to end_date (inclusive).

        Args:
            next_date (date): The first date at which to start processing snow.
            end_date (date): The last date to process snow for.
        """
        if next_date is None:
            logger.warning(" The start_date is required to process viirs snow.")
            return
        if end_date is None:
            logger.warning(" The end_date is required to process viirs snow.")
            return
        if next_date >= end_date:
            logger.info("Processing of VIIRS snow data is up to date.")
            return
        today_datetime = datetime.now(tz=vancouver_tz)
        with tempfile.TemporaryDirectory() as temp_dir:
            # Get the bc_boundary.geojson in a temp_dir. This is expensive so we only want to do this once.
            logger.info("Downloading bc_boundary.geojson from S3.")
            await self._get_bc_boundary_from_s3(temp_dir)
            while next_date <= end_date:
                date_string = next_date.strftime("%Y-%m-%d")
                logger.info(f"Processing snow coverage data for date: {date_string}")
                tz_aware_datetime = datetime.combine(
                    next_date, datetime.min.time(), tzinfo=vancouver_tz
                )

                await self._process_viirs_snow(next_date, temp_dir)
                async with get_async_write_session_scope() as session:
                    processed_snow = ProcessedSnow(
                        for_date=tz_aware_datetime,
                        processed_date=today_datetime,
                        snow_source=SnowSourceEnum.viirs,
                    )
                    await save_processed_snow(session, processed_snow)
                logger.info(
                    f"Successfully processed VIIRS snow coverage data for date: {date_string}"
                )
                next_date = next_date + timedelta(days=1)

    async def _run_viirs_snow(self, args: argparse.Namespace):
        """Entry point for running the job."""
        if args.start_datetime is not None and args.end_datetime is not None:
            # Path for reprocessing snow coverage data with provided start and end dates.
            await self._run_viirs_snow_with_args(args)
        else:
            # Path for typical daily update of snow coverage data.
            await self._run_viirs_snow_default()


def main():
    """Kicks off asynchronous processing of VIIRS snow coverage data."""
    parser = argparse.ArgumentParser(description="Process snow coverage data by date")
    parser.add_argument(
        "-s", "--start_datetime", help="The first datetime to start processing snow for."
    )
    parser.add_argument("-e", "--end_datetime", help="The last datetime to process snow for.")

    args = parser.parse_args()

    try:
        # We don't want gdal to silently swallow errors.
        gdal.UseExceptions()
        logger.debug("Begin processing VIIRS snow coverage data.")

        bot = ViirsSnowJob()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(bot._run_viirs_snow(args))

        # Exit with 0 - success.
        sys.exit(os.EX_OK)
    except NoGranulesException as no_granules_exception:
        # This is an expected condition as availability of snow data sometimes lags by several days.
        logger.warning(no_granules_exception.message)
        sys.exit(os.EX_OK)
    except Exception as exception:
        # Exit non 0 - failure.
        logger.error(
            "An error occurred while processing VIIRS snow coverage data.", exc_info=exception
        )
        rc_message = ":scream: Encountered an error while processing VIIRS snow data."
        send_rocketchat_notification(rc_message, exception)
        sys.exit(os.EX_SOFTWARE)


if __name__ == "__main__":
    configure_logging()
    main()
