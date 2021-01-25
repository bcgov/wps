""" Code for generating c-haines charts from grib files.

Process:
- Open grib files.
- Calculate c-haines in in memory raster layer.
- Polygonize the raster to a geojson data source.
NEXT:
- Load geojson, iterating through and saving it in the database.
- Simplify polygons.
- Load geojson from API and display in web map.
- Download all grib files for model run.
"""
from typing import Final
import os
from datetime import datetime, timezone, timedelta
import tempfile
import json
import logging
import struct
import numpy
import gdal
import ogr
from sqlalchemy.orm import Session
from shapely.ops import transform
from shapely.geometry import shape
from pyproj import CRS, Transformer, Proj
from app import configure_logging
from app.weather_models import ModelEnum, ProjectionEnum
from app.weather_models.process_grib import (get_transformer, GEO_CRS,
                                             get_dataset_geometry, calculate_geographic_coordinate)
from app.db.models import CHainesPoly, CHainesPrediction, CHainesModelRun, PredictionModel
from app.db.crud.weather_models import get_prediction_model
from app.db.crud.c_haines import (
    get_c_haines_model_run, get_c_haines_prediction, get_or_create_c_haines_model_run)
from app.time_utils import get_utc_now
from app.weather_models.env_canada import (get_model_run_hours,
                                           get_file_date_part, adjust_model_day, download)
import app.db.database

logger = logging.getLogger(__name__)


class BoundingBoxChecker():
    """ Class used to check if a given raster coordinate lies within a specified
    geographic bounding box. """

    def __init__(self, geo_bounding_box, padf_transform, raster_to_geo_transformer):
        self.geo_bounding_box = geo_bounding_box
        self.padf_transform = padf_transform
        self.raster_to_geo_transformer = raster_to_geo_transformer
        self.good_x = dict()
        self.check_cache = False

    def _is_inside_using_cache(self, raster_x, raster_y):
        good_y = self.good_x.get(raster_x)
        return good_y and raster_y in good_y

    def is_inside(self, raster_x, raster_y):
        """ Check if raster coordinate is inside the geographic bounding box """
        # Try to use the cached results.
        if self.check_cache:
            return self._is_inside_using_cache(raster_x, raster_y)
        # Calculate lat/long and check bounds.
        # NOTE: This is a very slow calculation - that's why we cache the results.
        lon, lat = calculate_geographic_coordinate(
            (raster_x, raster_y),
            self.padf_transform,
            self.raster_to_geo_transformer)
        lon0 = self.geo_bounding_box[0][0]
        lat0 = self.geo_bounding_box[0][1]
        lon1 = self.geo_bounding_box[1][0]
        lat1 = self.geo_bounding_box[1][1]
        if lon > lon0:
            if lon < lon1:
                if lat < lat0:
                    if lat > lat1:
                        good_y = self.good_x.get(raster_x)
                        if not good_y:
                            good_y = set()
                            self.good_x[raster_x] = good_y
                        good_y.add(raster_y)
                        return True
        return False


def get_prediction_date(model_run_timestamp, hour) -> datetime:
    """ Construct the part of the filename that contains the model run date
    """
    return model_run_timestamp + timedelta(hours=hour)


def model_prediction_hour_iterator(model: ModelEnum):
    if model == ModelEnum.GDPS:
        for hour in range(0, 241, 3):
            yield hour
    elif model == ModelEnum.RDPS:
        for hour in range(0, 85):
            yield hour
    elif model == ModelEnum.HRDPS:
        for hour in range(0, 49):
            yield hour
    else:
        raise Exception('uhnaldede model')


def make_model_run_base_url(model: ModelEnum, hh: str, hhh: str):
    if model == ModelEnum.GDPS:
        return 'https://dd.weather.gc.ca/model_gem_global/15km/grib2/lat_lon/{}/{}/'.format(
            hh, hhh)
    elif model == ModelEnum.RDPS:
        return 'https://dd.weather.gc.ca/model_gem_regional/10km/grib2/{}/{}/'.format(
            hh, hhh
        )
    elif model == ModelEnum.HRDPS:
        return 'https://dd.weather.gc.ca/model_hrdps/continental/grib2/{}/{}/'.format(
            hh, hhh)
    raise Exception('unsuported model')


def make_model_run_filename(model: ModelEnum, level: str, date: str, hh: str, hhh: str):
    if model == ModelEnum.GDPS:
        return 'CMC_glb_{}_latlon.15x.15_{}{}_P{}.grib2'.format(level, date, hh, hhh)
    elif model == ModelEnum.RDPS:
        return 'CMC_reg_{}_ps10km_{}{}_P{}.grib2'.format(
            level, date, hh, hhh)
    elif model == ModelEnum.HRDPS:
        return 'CMC_hrdps_continental_{level}_ps2.5km_{date}{hh}_P{hhh}-00.grib2'.format(
            level=level, date=date, hh=hh, hhh=hhh)
    raise Exception('unsupported model')


def make_model_levels(model: ModelEnum):
    if model == ModelEnum.HRDPS:
        return ['TMP_ISBL_0700', 'TMP_ISBL_0850', 'DEPR_ISBL_0850']
    return ['TMP_ISBL_700', 'TMP_ISBL_850', 'DEPR_ISBL_850']


def make_model_run_download_urls(model: ModelEnum,
                                 now: datetime,
                                 model_run_hour: int,
                                 prediction_hour: int):
    """ Yield urls to download GDPS (global) model runs """

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

    urls = {
        'model_run_timestamp': model_run_timestamp,
        'prediction_timestamp': get_prediction_date(model_run_timestamp, prediction_hour)
    }
    for level in levels:
        filename = make_model_run_filename(model, level, date, hh, hhh)
        urls[level] = base_url + filename
    return urls


def read_scanline(band, yoff):
    """ Read a band scanline, returning an array of values. """
    scanline = band.ReadRaster(xoff=0, yoff=yoff,
                               xsize=band.XSize, ysize=1,
                               buf_xsize=band.XSize, buf_ysize=1,
                               buf_type=gdal.GDT_Float32)
    return struct.unpack('f' * band.XSize, scanline)


def calculate_c_haines_index(t700: float, t850: float, td850: float):
    """ Given temperature and dew points values, calculate c-haines.  """
    # pylint: disable=invalid-name

    # Temperature depression term (this indicates atmospheric instability).
    # Temperature at 850mb - Temperature at 700mb.
    ca = (t850-t700)/2-2
    # Dew point depression term (this indicates how dry the air is).
    cb = td850/3-1

    # This part limits the extent to which dry air is able to affect the overall index.
    # If there is very dry air (big difference between dew point temperature and temperature),
    # we want to limit to overall effect on the index, since if there's no atmospheric
    # instability, that dry air isn't going anywhere.
    if cb > 9:
        cb = 9
    elif cb > 5:
        cb = 5 + (cb-5)/2
    ch = ca + cb

    return ch


def get_bucket_value(ch):
    # OZ BUCKET
    # if ch < 0:
    #     return 0
    # if ch < 5:
    #     return 1
    # if ch < 8:
    #     return 2
    # if ch < 10:
    #     return 3
    # if ch < 12:
    #     return 4
    # return 5

    # NEW BUCKET
    # 0 - 4 : low
    if ch < 4:
        return 0
    # 4 - 8 : moderate
    if ch < 8:
        return 1
    # 8 - 11 : high
    if ch < 11:
        return 2
    # 11 + Extreme
    return 3

    # OLD BUCKET
    # # 0 - 7 (Very low, low)
    # if ch < 7:
    #     level = 0
    # # 7 - 9 (Moderate)
    # elif ch < 9:
    #     level = 1
    # # 9 - 11 (High to very high)
    # elif ch < 11:
    #     level = 2
    # # 11 and up (Very high)
    # else:
    #     level = 3


def calculate_c_haines_data(
        grib_tmp_700: gdal.Dataset,
        grib_tmp_850: gdal.Dataset,
        grib_dew_850: gdal.Dataset):
    """ Given grib data sets for temperature and dew point, create array of data containing
    c-haines indices and mask """
    logger.info('calculting c-haines data...')

    # Load the raster data.
    tmp_850_raster_band = grib_tmp_850.GetRasterBand(1)
    tmp_700_raster_band = grib_tmp_700.GetRasterBand(1)
    dew_850_raster_band = grib_dew_850.GetRasterBand(1)

    c_haines_data: Final = []
    mask_data: Final = []

    # Assume they're all using the same number of rows/cols.
    rows: Final = tmp_850_raster_band.YSize
    cols: Final = tmp_850_raster_band.XSize

    lowest = None
    highest = None

    # Iterate through rows.
    for y_row_index in range(rows):

        chaines_row = []
        mask_row = []
        # Read the scanlines.
        row_tmp_700 = read_scanline(tmp_700_raster_band, y_row_index)
        row_tmp_850 = read_scanline(tmp_850_raster_band, y_row_index)
        row_dew_850 = read_scanline(dew_850_raster_band, y_row_index)

        # TODO: Look at using numpy to iterate through this faster.
        # Iterate through values in row.
        for x_column_index, (t700, t850, td850) in enumerate(zip(row_tmp_700, row_tmp_850, row_dew_850)):

            if bound_checker.is_inside(x_column_index, y_row_index):
                # pylint: disable=invalid-name
                ch = calculate_c_haines_index(t700, t850, td850)

                if lowest is None:
                    lowest = ch
                if highest is None:
                    highest = ch
                if ch < lowest:
                    lowest = ch
                if ch > highest:
                    highest = ch

                # We're not interested in such finely grained results, so
                # we bucket them together as such:
                level = get_bucket_value(ch)
                chaines_row.append(level)

                # We ignore level 0
                if level == 0:
                    mask_row.append(0)
                else:
                    mask_row.append(1)
            else:
                mask_row.append(0)
                chaines_row.append(0)

        c_haines_data.append(chaines_row)
        mask_data.append(mask_row)

    # print('lowest c-haines: {}'.format(lowest))
    # print('highest c-haines: {}'.format(highest))

    # TODO: look at creating numpy arrays from the get go
    return numpy.array(c_haines_data), numpy.array(mask_data), rows, cols


def save_data_as_tiff(
        c_haines_data: numpy.ndarray,
        target_filename: str,
        rows: int,
        cols: int,
        source_projection,
        source_geotransform):
    logger.info('saving output as tiff %s...', target_filename)
    driver = gdal.GetDriverByName("GTiff")
    outdata = driver.Create(target_filename, cols, rows, 1, gdal.GDT_Byte)
    outdata.SetProjection(source_projection)
    outdata.SetGeoTransform(source_geotransform)

    colors = gdal.ColorTable()

    # for i in range(255):
    #     colors.SetColorEntry(i, (i+50, i+50, i+50))
    # green
    colors.SetColorEntry(0, (0, 255, 0))
    # yellow
    colors.SetColorEntry(1, (255, 255, 0))
    # orange
    colors.SetColorEntry(2, (255, 164, 0))
    # red
    colors.SetColorEntry(3, (255, 0, 0))

    band = outdata.GetRasterBand(1)
    band.SetRasterColorTable(colors)
    band.SetRasterColorInterpretation(gdal.GCI_PaletteIndex)

    band.WriteArray(numpy.array(c_haines_data))
    outdata.FlushCache()


# def convert_to_polygon(ch_data: numpy.ndarray,
#                        mask_data: numpy.ndarray,
#                        projection,
#                        geotransform,
#                        rows: int,
#                        cols: int):
#     """ This doesn't work """

#     mem_driver = gdal.GetDriverByName('MEM')

#     # Create data band.
#     data_ds = mem_driver.Create('memory', cols, rows, 1, gdal.GDT_Byte)
#     data_ds.SetProjection(projection)
#     data_ds.SetGeoTransform(geotransform)
#     data_band = data_ds.GetRasterBand(1)
#     data_band.WriteArray(ch_data)

#     # Create mask band.
#     mask_ds = mem_driver.Create('memory', cols, rows, 1, gdal.GDT_Byte)
#     mask_ds.SetProjection(projection)
#     mask_ds.SetGeoTransform(geotransform)
#     mask_band = mask_ds.GetRasterBand(1)
#     mask_band.WriteArray(mask_data)

#     # Flush.
#     data_ds.FlushCache()
#     mask_ds.FlushCache()

#     # Create polygon data source
#     # polygon_ds = mem_driver.Create('memory', cols, rows, 1, gdal.GDT_Byte)
#     # ogr_mem_driver = ogr.GetDriverByName('MEMORY')
#     polygon_ds = mem_driver.CreateDataSource('memdata')
#     dst_layer = polygon_ds.CreateLayer('C-Haines', srs=None)
#     field_name = ogr.FieldDefn("index", ogr.OFTInteger)
#     field_name.SetWidth(24)
#     dst_layer.CreateField(field_name)
#     # Turn the rasters into polygons
#     gdal.Polygonize(data_band, mask_band, dst_layer, 0, [], callback=None)
#     polygon_ds.FlushCache()

#     del data_ds, mask_ds

#     return dst_layer


def save_data_as_geojson(
        ch_data: numpy.ndarray,
        mask_data: numpy.ndarray,
        source_projection,
        source_geotransform,
        rows: int,
        cols: int,
        target_filename: str):
    """ Save data as geojson polygon """
    logger.info('saving output as geojson %s...', target_filename)

    mem_driver = gdal.GetDriverByName('MEM')

    # Create data band.
    data_ds = mem_driver.Create('memory', cols, rows, 1, gdal.GDT_Byte)
    data_ds.SetProjection(source_projection)
    data_ds.SetGeoTransform(source_geotransform)
    data_band = data_ds.GetRasterBand(1)
    data_band.WriteArray(ch_data)

    # Create mask band.
    mask_ds = mem_driver.Create('memory', cols, rows, 1, gdal.GDT_Byte)
    mask_ds.SetProjection(source_projection)
    mask_ds.SetGeoTransform(source_geotransform)
    mask_band = mask_ds.GetRasterBand(1)
    mask_band.WriteArray(mask_data)

    # Flush.
    data_ds.FlushCache()
    mask_ds.FlushCache()

    # Save as geojson
    geojson_driver = ogr.GetDriverByName('GeoJSON')
    dst_ds = geojson_driver.CreateDataSource(target_filename)

    # Setting projection on the data source is not possible:
    # dst_ds.SetProjection(GEO_CRS.to_string())

    srs = ogr.osr.SpatialReference()
    srs.SetWellKnownGeogCS("WGS84")
    print('IsGeographic: {}'.format(srs.IsGeographic()))
    # setting srs on layer, doesn't help.
    dst_layer = dst_ds.CreateLayer('C-Haines', srs=srs)
    field_name = ogr.FieldDefn("severity", ogr.OFTInteger)
    field_name.SetWidth(24)
    dst_layer.CreateField(field_name)
    # Turn the rasters into polygons
    gdal.Polygonize(data_band, mask_band, dst_layer, 0, [], callback=None)
    dst_ds.FlushCache()

    # Explicitly clean up (is this needed?)
    del dst_ds, data_ds, mask_ds


def save_geojson_to_database(session: Session,
                             source_projection, filename: str,
                             prediction_timestamp: datetime,
                             model_run: CHainesModelRun):
    """ Open geojson file, iterate through features, saving them into the
    databse.
    """
    logger.info('saving geojson %s to database...', filename)
    # Open the geojson file.
    with open(filename) as file:
        data = json.load(file)

    # Source coordinate system, must match source data.
    proj_from = Proj(projparams=source_projection)
    # Destination coordinate systems (NAD83, geographic coordinates)
    proj_to = Proj('epsg:4269')
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
            severity=feature['properties']['severity'],
            c_haines_prediction=prediction)
        # Add to current session.
        session.add(polygon)
    # Only commit once we have everything.
    session.commit()
    # TODO: simplify geometry: https://shapely.readthedocs.io/en/stable/manual.html#object.simplify


# def assertSameProjectionAndTransformation(a, b, c):
#     # print(a.GetProjection())
#     pass


def generate_and_store_c_haines(
        session: Session,
        filename_tmp_700: str,
        filename_tmp_850: str,
        filename_dew_850: str,
        prediction_timestamp: datetime,
        model_run: CHainesModelRun):
    # Open the grib files.
    grib_tmp_700 = gdal.Open(filename_tmp_700, gdal.GA_ReadOnly)
    grib_tmp_850 = gdal.Open(filename_tmp_850, gdal.GA_ReadOnly)
    grib_dew_850 = gdal.Open(filename_dew_850, gdal.GA_ReadOnly)

    # assertSameProjectionAndTransformation(grib_tmp_700, grib_tmp_850, grib_dew_850)

    # Assume all three the grib files are using the same projection and transformation.
    source_projection = grib_tmp_850.GetProjection()
    source_geotransform = grib_tmp_850.GetGeoTransform()
    padf_transform = get_dataset_geometry(grib_tmp_700)

    # S->N 46->70
    # E->W -110->-140
    top_left_geo = (-140, 70)
    bottom_right_geo = (-110, 46)
    geographic_bounding_box = (top_left_geo, bottom_right_geo)
    crs = CRS.from_string(source_projection)
    # Create a transformer to go from whatever the raster is, to geographic coordinates.
    raster_to_geo_transformer = get_transformer(crs, GEO_CRS)
    global bound_checker
    if not bound_checker:
        logger.info('re-creating bound checker')
        bound_checker = BoundingBoxChecker(
            geographic_bounding_box, padf_transform, raster_to_geo_transformer)
    else:
        logger.info('re-using bound checker')
        bound_checker.check_cache = True

    c_haines_data, mask_data, rows, cols = calculate_c_haines_data(
        grib_tmp_700, grib_tmp_850, grib_dew_850)

    # Expictly release the grib files - they take a lot of memory. (Is this needed?)
    del grib_tmp_700, grib_tmp_850, grib_dew_850

    # Save to tiff (for easy debugging)
    # save_data_as_tiff(
    #     c_haines_data, 'c-haines_{}_{}.tiff'.format(
    #         model_run_timestamp.isoformat(), prediction_timestamp.isoformat()),
    #     rows, cols, projection, geotransform)

    # Save to geojson
    with tempfile.TemporaryDirectory() as tmp_path:
        json_filename = os.path.join(os.getcwd(), tmp_path, 'c-haines.geojson')
        save_data_as_geojson(
            c_haines_data,
            mask_data,
            source_projection,
            source_geotransform,
            rows,
            cols,
            json_filename)

        save_geojson_to_database(session, source_projection, json_filename,
                                 prediction_timestamp,
                                 model_run)


def local_test():
    # filename_tmp_700 = '/home/sybrand/Workspace/wps/api/scripts/CMC_glb_TMP_ISBL_700_latlon.15x.15_2020122200_P000.grib2'
    # filename_tmp_850 = '/home/sybrand/Workspace/wps/api/scripts/CMC_glb_TMP_ISBL_850_latlon.15x.15_2020122200_P000.grib2'
    # filename_dew_850 = '/home/sybrand/Workspace/wps/api/scripts/CMC_glb_DEPR_ISBL_850_latlon.15x.15_2020122200_P000.grib2'

    filename_tmp_700 = '/home/sybrand/Downloads/Work/CMC_glb_TMP_ISBL_700_latlon.15x.15_2021011800_P123.grib2'
    filename_tmp_850 = '/home/sybrand/Downloads/Work/CMC_glb_TMP_ISBL_850_latlon.15x.15_2021011800_P123.grib2'
    filename_dew_850 = '/home/sybrand/Downloads/Work/CMC_glb_DEPR_ISBL_850_latlon.15x.15_2021011800_P123.grib2'
    model_run_timestamp = datetime(year=2021, month=1, day=18, hour=0, tzinfo=timezone.utc)
    prediction_timestamp = datetime(year=2021, month=1, day=23, hour=3, tzinfo=timezone.utc)

    # filename_tmp_700 = '/home/sybrand/Downloads/Work/CMC_hrdps_continental_TMP_ISBL_0700_ps2.5km_2021012500_P000-00.grib2'
    # filename_tmp_850 = '/home/sybrand/Downloads/Work/CMC_hrdps_continental_TMP_ISBL_0850_ps2.5km_2021012500_P000-00.grib2'
    # filename_dew_850 = '/home/sybrand/Downloads/Work/CMC_hrdps_continental_DEPR_ISBL_0850_ps2.5km_2021012500_P000-00.grib2'
    model_run_timestamp = datetime(year=2021, month=1, day=25, hour=0, tzinfo=timezone.utc)
    prediction_timestamp = datetime(year=2021, month=1, day=25, hour=0, tzinfo=timezone.utc)

    session = app.db.database.get_write_session()
    prediction_model = get_prediction_model(session, ModelEnum.HRDPS, ProjectionEnum.HIGH_RES_CONTINENTAL)
    model_run = get_or_create_c_haines_model_run(session, model_run_timestamp, prediction_model)

    generate_and_store_c_haines(
        session,
        filename_tmp_700,
        filename_tmp_850,
        filename_dew_850,
        prediction_timestamp,
        model_run)


def record_exists(
        session,
        model_run: CHainesModelRun,
        prediction_timestamp: datetime):
    """ Check if we have a c-haines record """
    result = get_c_haines_prediction(session, model_run, prediction_timestamp)
    return result.count() > 0


def generate(model: ModelEnum, projection: ProjectionEnum):
    session = app.db.database.get_write_session()
    prediction_model = get_prediction_model(session, model, projection)
    utc_now = get_utc_now()
    for model_hour in get_model_run_hours(model):
        model_run = None
        for prediction_hour in model_prediction_hour_iterator(model):
            urls = make_model_run_download_urls(model, utc_now, model_hour, prediction_hour)
            if not model_run:
                model_run = get_or_create_c_haines_model_run(
                    session, urls['model_run_timestamp'], prediction_model)
            if record_exists(session, model_run, urls['prediction_timestamp']):
                logger.info('already downloaded %s - %s',
                            urls['model_run_timestamp'], urls['prediction_timestamp'])
                continue

        # for urls in get_global_model_run_download_urls(utc_now, model_hour):
            # TODO: check if we haven't already downloaded this
            with tempfile.TemporaryDirectory() as tmp_path:
                if model == ModelEnum.HRDPS:
                    filename_tmp_700 = download(urls['TMP_ISBL_0700'], tmp_path)
                    filename_tmp_850 = download(urls['TMP_ISBL_0850'], tmp_path)
                    filename_dew_850 = download(urls['DEPR_ISBL_0850'], tmp_path)
                else:
                    filename_tmp_700 = download(urls['TMP_ISBL_700'], tmp_path)
                    filename_tmp_850 = download(urls['TMP_ISBL_850'], tmp_path)
                    filename_dew_850 = download(urls['DEPR_ISBL_850'], tmp_path)

                if filename_tmp_700 and filename_tmp_850 and filename_dew_850:
                    generate_and_store_c_haines(
                        session,
                        filename_tmp_700,
                        filename_tmp_850,
                        filename_dew_850,
                        urls['prediction_timestamp'],
                        model_run)
                else:
                    logger.warning('failed to download all files')


def main():
    global bound_checker
    models = (
        (ModelEnum.GDPS, ProjectionEnum.LATLON_15X_15),
        (ModelEnum.RDPS, ProjectionEnum.REGIONAL_PS),
        (ModelEnum.HRDPS, ProjectionEnum.HIGH_RES_CONTINENTAL),)
    for model, projection in models:
        bound_checker = None
        generate(model, projection)


if __name__ == "__main__":
    configure_logging()
    bound_checker = None
    main()
    # local_test()
