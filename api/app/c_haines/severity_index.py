""" Logic pertaining to the generation of c_haines severity index from GDAL datasets.
"""
import os
import io
from datetime import datetime, timezone, timedelta
from typing import Final, Tuple, Generator, Union, List
from contextlib import contextmanager
import tempfile
import logging
import json
from osgeo import gdal, ogr
import numpy
from pyproj import Transformer, Proj
from shapely.ops import transform
from minio import Minio
from shapely.geometry import shape, mapping
from sqlalchemy.orm import Session
from app.utils.s3 import get_minio_client, object_exists
from app.utils.time import get_utc_now
from app.db.models.c_haines import CHainesPoly, CHainesPrediction, CHainesModelRun, get_severity_string
from app.weather_models import ModelEnum, ProjectionEnum
from app.geospatial import NAD83, WGS84
from app.weather_models.env_canada import (get_model_run_hours,
                                           get_file_date_part, adjust_model_day, download,
                                           UnhandledPredictionModelType)
from app.c_haines.c_haines_index import CHainesGenerator
from app.c_haines import GDALData
from app.c_haines.object_store import (ObjectTypeEnum, generate_full_object_store_path)
from app.c_haines.kml import save_as_kml_to_s3


logger = logging.getLogger(__name__)


def get_severity(c_haines_index) -> int:
    """ Return the "severity" of the continuous haines index.

    Fire behaviour analysts are typically only concerned if there's a high
    or extreme index - so the c-haines values are lumped together by severity.

    The severity used here is fairly arbitrary - there's no standard in place.
    """
    # 0 - 4 : low
    if c_haines_index < 4:
        return 0
    # 4 - 8 : moderate
    if c_haines_index < 8:
        return 1
    # 8 - 11 : high
    if c_haines_index < 11:
        return 2
    # 11 + Extreme
    return 3


@contextmanager
def open_gdal(filename_tmp_700: str,
              filename_tmp_850: str,
              filename_dew_850: str) -> Generator[GDALData, None, None]:
    """ Open gdal, and yield handy object containing all the data """
    try:
        # Open the datasets.
        grib_tmp_700 = gdal.Open(filename_tmp_700, gdal.GA_ReadOnly)
        grib_tmp_850 = gdal.Open(filename_tmp_850, gdal.GA_ReadOnly)
        grib_dew_850 = gdal.Open(filename_dew_850, gdal.GA_ReadOnly)
        # Yield handy object.
        yield GDALData(grib_tmp_700, grib_tmp_850, grib_dew_850)
    finally:
        # Clean up memory.
        del grib_tmp_700, grib_tmp_850, grib_dew_850


def get_prediction_date(model_run_timestamp, hour) -> datetime:
    """ Construct the part of the filename that contains the model run date
    """
    return model_run_timestamp + timedelta(hours=hour)


def model_prediction_hour_iterator(model: ModelEnum):
    """ Return a prediction hour iterator.
    Each model has a slightly different set of prediction hours. """
    if model == ModelEnum.GDPS:
        # GDPS goes out real far, but in 3 hour intervals.
        for hour in range(0, 241, 3):
            yield hour
    elif model == ModelEnum.RDPS:
        # RDPS goes out 3 1/2 days.
        for hour in range(0, 85):
            yield hour
    elif model == ModelEnum.HRDPS:
        # HRDPS goes out 2 days.
        for hour in range(0, 49):
            yield hour
    else:
        raise UnhandledPredictionModelType()


def make_model_run_base_url(model: ModelEnum, model_run_start: str, forecast_hour: str):
    """ Return the base url for the grib file.
    The location of the files differs slightly for each model. """
    if model == ModelEnum.GDPS:
        return 'https://dd.weather.gc.ca/model_gem_global/15km/grib2/lat_lon/{HH}/{hhh}/'.format(
            HH=model_run_start, hhh=forecast_hour)
    if model == ModelEnum.RDPS:
        return 'https://dd.weather.gc.ca/model_gem_regional/10km/grib2/{HH}/{hhh}/'.format(
            HH=model_run_start, hhh=forecast_hour
        )
    if model == ModelEnum.HRDPS:
        return 'https://dd.weather.gc.ca/model_hrdps/continental/grib2/{HH}/{hhh}/'.format(
            HH=model_run_start, hhh=forecast_hour)
    raise UnhandledPredictionModelType()


def make_model_run_filename(
        model: ModelEnum, level: str, date: str, model_run_start: str, forecast_hour: str):
    """ Return the filename of the grib file.
    The filename for each model differs slightly. """
    if model == ModelEnum.GDPS:
        return 'CMC_glb_{}_latlon.15x.15_{}{HH}_P{hhh}.grib2'.format(
            level, date, HH=model_run_start, hhh=forecast_hour)
    if model == ModelEnum.RDPS:
        return 'CMC_reg_{}_ps10km_{}{HH}_P{hhh}.grib2'.format(
            level, date, HH=model_run_start, hhh=forecast_hour)
    if model == ModelEnum.HRDPS:
        return 'CMC_hrdps_continental_{level}_ps2.5km_{date}{HH}_P{hhh}-00.grib2'.format(
            level=level, date=date, HH=model_run_start, hhh=forecast_hour)
    raise UnhandledPredictionModelType()


def make_model_levels(model: ModelEnum):
    """ Return list of layers. (The layers are named slightly differently for HRDPS)
    TMP_ISBL_0700 : Temperature at 700mb.
    TMP_ISBL_0850 : Temperature at 850mb.
    DEPR_ISBL_0850 : Dew point depression at 850mb.
    """
    if model == ModelEnum.HRDPS:
        return ['TMP_ISBL_0700', 'TMP_ISBL_0850', 'DEPR_ISBL_0850']
    return ['TMP_ISBL_700', 'TMP_ISBL_850', 'DEPR_ISBL_850']


def make_model_run_download_urls(model: ModelEnum,
                                 now: datetime,
                                 model_run_hour: int,
                                 prediction_hour: int) -> Tuple[dict, datetime, datetime]:
    """ Return urls to download model runs """

    # hh: model run start, in UTC [00, 12]
    # hhh: prediction hour [000, 003, 006, ..., 240]
    levels: Final = make_model_levels(model)
    # pylint: disable=invalid-name
    hh = '{:02d}'.format(model_run_hour)
    # For the global model, we have prediction at 3 hour intervals up to 240 hours.
    hhh = format(prediction_hour, '03d')

    base_url = make_model_run_base_url(model, hh, hhh)
    date = get_file_date_part(now, model_run_hour)

    adjusted_model_time = adjust_model_day(now, model_run_hour)
    model_run_timestamp = datetime(year=adjusted_model_time.year,
                                   month=adjusted_model_time.month,
                                   day=adjusted_model_time.day,
                                   hour=model_run_hour,
                                   tzinfo=timezone.utc)

    prediction_timestamp = get_prediction_date(model_run_timestamp, prediction_hour)
    urls = {}
    for level in levels:
        filename = make_model_run_filename(model, level, date, hh, hhh)
        urls[level] = base_url + filename

    return urls, model_run_timestamp, prediction_timestamp


class SourceInfo():
    """ Handy class to store source information in . """

    def __init__(self, projection, geotransform, rows: int, cols: int):
        self.projection: str = projection
        self.geotransform = geotransform
        self.rows: int = rows
        self.cols: int = cols


def create_in_memory_band(data: numpy.ndarray, source_info: SourceInfo):
    """ Create an in memory data band to represent a single raster layer.
    See https://gdal.org/user/raster_data_model.html#raster-band for a complete
    description of what a raster band is.
    """
    mem_driver = gdal.GetDriverByName('MEM')

    dataset = mem_driver.Create('memory', source_info.cols, source_info.rows, 1, gdal.GDT_Byte)
    dataset.SetProjection(source_info.projection)
    dataset.SetGeoTransform(source_info.geotransform)
    band = dataset.GetRasterBand(1)
    band.WriteArray(data)

    return dataset, band


def save_data_as_geojson(
        ch_data: numpy.ndarray,
        mask_data: numpy.ndarray,
        source_info: SourceInfo,
        target_filename: str):
    """ Save data as geojson polygon """
    logger.info('Saving output as geojson %s...', target_filename)

    # Create data band.
    data_ds, data_band = create_in_memory_band(
        ch_data, source_info)

    # Create mask band.
    mask_ds, mask_band = create_in_memory_band(
        mask_data, source_info)

    # Create a GeoJSON layer.
    geojson_driver = ogr.GetDriverByName('GeoJSON')
    dst_ds = geojson_driver.CreateDataSource(target_filename)
    dst_layer = dst_ds.CreateLayer('C-Haines')
    field_name = ogr.FieldDefn("severity", ogr.OFTInteger)
    field_name.SetWidth(24)
    dst_layer.CreateField(field_name)

    # Turn the rasters into polygons.
    gdal.Polygonize(data_band, mask_band, dst_layer, 0, [], callback=None)

    # Ensure that all data in the target dataset is written to disk.
    dst_ds.FlushCache()
    # Explicitly clean up (is this needed?)
    del dst_ds, data_ds, mask_ds


def save_geojson_to_database(session: Session,
                             source_projection, filename: str,
                             prediction_timestamp: datetime,
                             model_run: CHainesModelRun):
    """ Open geojson file, iterate through features, saving them into the
    database.
    """
    logger.info('Saving geojson for model run %s, prediction %s to database...',
                model_run.model_run_timestamp,  prediction_timestamp)
    # Open the geojson file.
    with open(filename) as file:
        data = json.load(file)

    # Source coordinate system, must match source data.
    proj_from = Proj(projparams=source_projection)
    # Destination coordinate systems (NAD83, geographic coordinates)
    proj_to = Proj(NAD83)
    project = Transformer.from_proj(proj_from, proj_to, always_xy=True)

    # Create a prediction record to hang everything off of:
    prediction = CHainesPrediction(model_run=model_run,
                                   prediction_timestamp=prediction_timestamp)
    session.add(prediction)
    # Convert each feature into a shapely geometry and save to database.
    for feature in data['features']:
        # Create polygon:
        source_geometry = shape(feature['geometry'])
        # Transform polygon from source to NAD83
        geometry = transform(project.transform, source_geometry)
        # Create data model object.
        polygon = CHainesPoly(
            geom=geometry.wkt,
            c_haines_index=get_severity_string(feature['properties']['severity']),
            c_haines_prediction=prediction)
        # Add to current session.
        session.add(polygon)
    # Only commit once we have everything.
    session.commit()


def generate_severity_data(c_haines_data):
    """ Generate severity index data, iterating over c-haines data.
    NOTE: Iterating to generate c-haines, and then iterating again to generate severity is a bit slower,
    but results in much cleaner code.
    """
    logger.info('Generating c-haines severity index data.')
    severity_data = []
    mask_data = []
    for row in c_haines_data:
        severity_row = []
        mask_row = []
        for cell in row:
            severity = get_severity(cell)
            severity_row.append(severity)
            # We ignore severity 0.
            if severity == 0:
                mask_row.append(0)
            else:
                mask_row.append(1)
        severity_data.append(severity_row)
        mask_data.append(mask_row)
    return numpy.array(severity_data), numpy.array(mask_data)


class EnvCanadaPayload():
    """ Handy class to store payload information in . """

    def __init__(self):
        self.filename_tmp_700: str = None
        self.filename_tmp_850: str = None
        self.filename_dew_850: str = None
        self.model: ModelEnum = None
        self.model_run_timestamp: datetime = None
        self.prediction_timestamp: datetime = None


def re_project_and_classify_geojson(source_json_filename: str,
                                    source_projection: str) -> dict:
    """ Given a geojson file in a specified projection
    - order by severity.
    - re-project to wgs84.
    - re-classify the "severity index" as a c_haines_index string.
    - return as a dictionary
    """
    proj_from = Proj(projparams=source_projection)
    proj_to = Proj(WGS84)
    project = Transformer.from_proj(proj_from, proj_to, always_xy=True)
    with open(source_json_filename) as source_file:
        geojson_data = json.load(source_file)
        # We need to sort the geojson by severity.
        geojson_data['features'].sort(key=lambda feature: feature['properties']['severity'])
        # Iterate through features.
        for feature in geojson_data['features']:
            # Replace "severity" with c-haines.
            feature['properties'] = {"c_haines_index": get_severity_string(feature['properties']['severity'])}
            # Re-project to WGS84
            source_geometry = shape(feature['geometry'])
            geometry = transform(project.transform, source_geometry)
            geojson_geometry = mapping(geometry)
            feature['geometry']['coordinates'] = geojson_geometry['coordinates']
    return geojson_data


def save_as_geojson_to_s3(client: Minio,  # pylint: disable=too-many-arguments
                          bucket: str,
                          source_json_filename: str,
                          source_projection: str,
                          prediction_model: ModelEnum,
                          model_run_timestamp: datetime,
                          prediction_timestamp: datetime):
    """ Given a geojson file, ensure it's in the correct projection and then store to S3 """
    target_path = generate_full_object_store_path(
        prediction_model, model_run_timestamp, prediction_timestamp, ObjectTypeEnum.GEOJSON)
    # let's save some time, and check if the file doesn't already exists.
    # it's super important we do this, since there are many c-haines cronjobs running in dev, all
    # pointing to the same s3 bucket.
    if object_exists(client, bucket, target_path):
        logger.info('json (%s) already exists - skipping', target_path)
        return

    # re-project the geojson file from whatever it was, to WGS84.
    re_projected_data = re_project_and_classify_geojson(source_json_filename, source_projection)

    with io.StringIO() as sio:
        json.dump(re_projected_data, sio)
        # smash it into binary
        sio.seek(0)
        bio = io.BytesIO(sio.read().encode('utf8'))
        # get file size.
        size = bio.seek(0, io.SEEK_END)
        # go back to start
        bio.seek(0)
        # smash it into the object store.
        logger.info('uploading %s (%s)', target_path, size)
        client.put_object(bucket, target_path, bio, size)


class CHainesSeverityGenerator():
    """ Class responsible for orchestrating the generation of Continous Haines severity
    index polygons.

    Steps for generation of severity level as follows:
    1) Download grib files.
    2) Iterate through raster rows, generating an in memory raster containing c-haines severity indices.
    3) Turn raster data into polygons, storing in intermediary GeoJSON file.
    4) Write polygons to database.
    """

    def __init__(self, model: ModelEnum, projection: ProjectionEnum, session: Session):
        self.model = model
        self.projection = projection
        self.c_haines_generator = CHainesGenerator()
        self.session = session
        client, bucket = get_minio_client()
        self.client: Minio = client
        self.bucket: str = bucket

    def _collect_payload(self,
                         urls: dict,
                         model: ModelEnum,
                         model_run_timestamp: datetime,
                         prediction_timestamp: datetime,
                         temporary_path: str) -> Union[EnvCanadaPayload, None]:
        """ Collect all the different things that make up our payload: our downloaded files,
        model run, and prediction timestamp. """

        def _download_files(urls: dict,
                            model: ModelEnum,
                            temporary_path: str) -> Union[List[str], None]:
            """ Try to download all the files """
            filenames = []
            for key in make_model_levels(model):
                # Try to download this file.
                filename = download(urls[key], temporary_path)
                if not filename:
                    # If we fail to download one of files, quit, don't try the others.
                    logger.warning('failed to download %s', urls[key])
                    return None
                filenames.append(filename)
            return filenames

        filenames = _download_files(urls, self.model, temporary_path)
        if filenames:
            filename_tmp_700, filename_tmp_850, filename_dew_850 = filenames
            payload = EnvCanadaPayload()
            payload.filename_tmp_700 = filename_tmp_700
            payload.filename_tmp_850 = filename_tmp_850
            payload.filename_dew_850 = filename_dew_850
            payload.model = model
            payload.model_run_timestamp = model_run_timestamp
            payload.prediction_timestamp = prediction_timestamp
            return payload
        return None

    def _assets_exist(self, model: ModelEnum,
                      model_run_timestamp: datetime,
                      prediction_timestamp: datetime) -> bool:
        """ Return True if kml and geojson assets already exist, otherwise False """
        kml_path = generate_full_object_store_path(
            model,
            model_run_timestamp,
            prediction_timestamp,
            ObjectTypeEnum.KML)
        kml_exists = object_exists(self.client, self.bucket, kml_path)

        json_path = generate_full_object_store_path(
            model,
            model_run_timestamp,
            prediction_timestamp,
            ObjectTypeEnum.GEOJSON)
        json_exists = object_exists(self.client, self.bucket, json_path)

        return kml_exists and json_exists

    def _get_payloads(self, temporary_path) -> Generator[EnvCanadaPayload, None, None]:
        """ Iterator that yields the next to process. """
        utc_now = get_utc_now()
        for model_hour in get_model_run_hours(self.model):
            for prediction_hour in model_prediction_hour_iterator(self.model):

                urls, model_run_timestamp, prediction_timestamp = make_model_run_download_urls(
                    self.model, utc_now, model_hour, prediction_hour)

                # If the GeoJSON and the KML already exist, then we can skip this one.
                if self._assets_exist(self.model,
                                      model_run_timestamp,
                                      prediction_timestamp):
                    logger.info('%s: already processed %s-%s',
                                self.model,
                                model_run_timestamp, prediction_timestamp)
                    continue
                # TODO: ^^ section above soon to be redundant.

                payload = self._collect_payload(urls,
                                                self.model,
                                                model_run_timestamp,
                                                prediction_timestamp,
                                                temporary_path)
                if payload:
                    yield payload
                else:
                    # If you didn't get one of them - you probably won't get the rest either!
                    logger.info('Failed to download one of the model files - skipping the rest')
                    return

    def _generate_c_haines_data(
            self,
            payload: EnvCanadaPayload):

        # Open the grib files.
        with open_gdal(payload.filename_tmp_700,
                       payload.filename_tmp_850,
                       payload.filename_dew_850) as source_data:
            # Generate c_haines data
            c_haines_data = self.c_haines_generator.generate_c_haines(source_data)
            # Store the projection and geotransform for later.
            projection = source_data.grib_tmp_700.GetProjection()
            geotransform = source_data.grib_tmp_700.GetGeoTransform()
            # Store the dimensions for later.
            band = source_data.grib_tmp_700.GetRasterBand(1)
            rows = band.YSize
            cols = band.XSize
            # Package source info nicely.
            source_info = SourceInfo(projection=projection,
                                     geotransform=geotransform, rows=rows, cols=cols)

        return c_haines_data, source_info

    def _persist_severity_data(self,
                               payload: EnvCanadaPayload,
                               c_haines_severity_data,
                               c_haines_mask_data,
                               source_info: SourceInfo):
        with tempfile.TemporaryDirectory() as temporary_path:
            json_filename = os.path.join(os.getcwd(), temporary_path, 'c-haines.geojson')
            save_data_as_geojson(
                c_haines_severity_data,
                c_haines_mask_data,
                source_info,
                json_filename)

            # if payload.model == ModelEnum.RDPS or payload.model == ModelEnum.HRDPS:
            #     print(source_info.projection)
            #     import shutil
            #     shutil.copyfile(json_filename, './source_file.json')
            #     raise Exception('blah!')

            save_as_kml_to_s3(self.client, self.bucket, json_filename, source_info.projection,
                              payload.model,
                              payload.model_run_timestamp, payload.prediction_timestamp)

            save_as_geojson_to_s3(self.client, self.bucket, json_filename, source_info.projection,
                                  payload.model,
                                  payload.model_run_timestamp, payload.prediction_timestamp)

    def generate(self):
        """ Entry point for generating and storing c-haines severity index. """
        # Iterate through payloads that need processing.
        with tempfile.TemporaryDirectory() as temporary_path:
            for payload in self._get_payloads(temporary_path):
                # Generate the c_haines data.
                c_haines_data, source_info = self._generate_c_haines_data(payload)
                # Generate the severity index and mask data.
                c_haines_severity_data, c_haines_mask_data = generate_severity_data(c_haines_data)
                # We're done with the c_haines data, so we can clean up some memory.
                del c_haines_data
                # Save to s3.
                self._persist_severity_data(payload,
                                            c_haines_severity_data,
                                            c_haines_mask_data,
                                            source_info)
                # Delete temporary files
                os.remove(payload.filename_dew_850)
                os.remove(payload.filename_tmp_700)
                os.remove(payload.filename_tmp_850)
