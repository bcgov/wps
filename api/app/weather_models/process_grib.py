""" Read a grib file, and store values relevant to weather stations in database.
"""

from datetime import datetime
import math
import struct
import logging
import logging.config
from typing import List, Tuple, Optional
from sqlalchemy.dialects.postgresql import array
from sqlalchemy.orm import Session
from osgeo import gdal
from pyproj import CRS, Transformer
from affine import Affine
import rasterio
from rasterio.io import DatasetReader
from app.geospatial import NAD83_CRS
from app.stations import get_stations_synchronously
from app.db.models.weather_models import (
    PredictionModel, PredictionModelRunTimestamp, ModelRunGridSubsetPrediction)
from app.db.crud.weather_models import (
    get_prediction_model, get_or_create_prediction_run, get_or_create_grid_subset)
from app.weather_models import ModelEnum, ProjectionEnum


logger = logging.getLogger(__name__)

GFS_000_HOURS_RASTER_BANDS = {
    'tmp_tgl_2': 580,
    'rh_tgl_2': 583,
    'u_comp_wind_10m': 585,
    'v_comp_wind_10m': 586
}
GFS_003_HOURS_RASTER_BANDS = {
    'tmp_tgl_2': 581,
    'rh_tgl_2': 584,
    'apcp_sfc_0': 596,  # or 597. Documentation doesn't specify difference
    'u_comp_wind_10m': 588,
    'v_comp_wind_10m': 589
}


class PredictionModelNotFound(Exception):
    """ Exception raised when specified model cannot be found in database. """


class DatabaseException(Exception):
    """ Exception raised to to database related issue. """


class ModelRunInfo():
    """ Information relation to a particular model run
    """

    def __init__(self, model_enum=None, projection=None, model_run_timestamp=None,
                 prediction_timestamp=None, variable_name=None):
        self.model_enum: Optional[ModelEnum] = model_enum
        self.projection: Optional[ProjectionEnum] = projection
        self.model_run_timestamp: Optional[datetime] = model_run_timestamp
        self.prediction_timestamp: Optional[datetime] = prediction_timestamp
        self.variable_name: Optional[str] = variable_name


def get_surrounding_grid(
        band: gdal.Dataset, x_index: int, y_index: int) -> Tuple[List[int], List[float]]:
    """ Get the grid and values surrounding a given station
    NOTE: Order of the points is super important! Vertices are ordered clockwise, values are also
    ordered clockwise.
    """
    # Read scanlines of the raster, build up the four points and corresponding values:
    scanline_one = band.ReadRaster(xoff=x_index, yoff=y_index, xsize=2, ysize=1,
                                   buf_xsize=2, buf_ysize=1, buf_type=gdal.GDT_Float32)
    row_one = struct.unpack('f' * 2, scanline_one)
    values = []
    values.extend(row_one)
    scanline_two = band.ReadRaster(xoff=x_index, yoff=y_index + 1, xsize=2, ysize=1,
                                   buf_xsize=2, buf_ysize=1, buf_type=gdal.GDT_Float32)
    row_two = struct.unpack('f' * 2, scanline_two)
    values.append(row_two[1])
    values.append(row_two[0])

    points = [[x_index, y_index], [x_index + 1, y_index],
              [x_index + 1, y_index + 1], [x_index, y_index + 1]]

    return points, values


def calculate_raster_coordinate(
        longitude: float,
        latitude: float,
        transform: Affine,
        transformer: Transformer):
    """ From a given longitude and latitude, calculate the raster coordinate corresponding to the
    top left point of the grid surrounding the given geographic coordinate.
    """
    # Because not all model types use EPSG:4269 projection, we first convert longitude and latitude
    # to whichever projection and coordinate system the grib file is using
    raster_long, raster_lat = transformer.transform(longitude, latitude)
    reverse = ~transform
    i_index, j_index = reverse * (raster_long, raster_lat)
    return (math.floor(i_index), math.floor(j_index))


def calculate_geographic_coordinate(point: Tuple[int],
                                    transform: Affine,
                                    transformer: Transformer):
    """ Calculate the geographic coordinates for a given points """
    x_coordinate, y_coordinate = transform * point
    lon, lat = transformer.transform(x_coordinate, y_coordinate)
    return (lon, lat)


def open_grib(filename: str) -> gdal.Dataset:
    """ Open grib file """
    # NOTE: What's the purpose of wrapping the gdal call in a function?
    return gdal.Open(filename, gdal.GA_ReadOnly)


def get_dataset_geometry(filename) -> Affine:
    """ Get the geometry info (origin and pixel size) of the dataset.

    GDAL 3.4.1 has a bug, and reports the wrong geometry for grib files, so
    dataset.GetGeoTransform() is unreliable.
    """
    source: DatasetReader = rasterio.open(filename)
    return source.transform


def get_transformer(crs_from, crs_to):
    """ Get an appropriate transformer - it's super important that always_xy=True
    is specified, otherwise the order in the CRS definition is honoured. """
    return Transformer.from_crs(crs_from, crs_to, always_xy=True)


def calculate_wind_speed_from_u_v(u: float, v: float):
    """ Return calculated wind speed from u and v components using formula
    wind_speed = sqrt(u^2 + v^2)

    What the heck is going on here?! See
    http://colaweb.gmu.edu/dev/clim301/lectures/wind/wind-uv
    """
    return math.sqrt(math.pow(u, 2) + math.pow(v, 2))


def calculate_wind_dir_from_u_v(u: float, v: float):
    """ Return calculated wind direction from u and v components using formula
    wind_direction = arctan(u, v) * 180/pi (in degrees)

    What the heck is going on here?! See
    http://colaweb.gmu.edu/dev/clim301/lectures/wind/wind-uv
    """
    calc = math.atan2(u, v) * 180 / math.pi
    # convert to meteorological convention of direction wind is coming from rather than
    # direction wind is going to
    calc += 180
    # must convert from trig coordinates to cardinal coordinates
    calc = 90 - calc
    return calc if calc > 0 else 360 + calc


class GribFileProcessor():
    """ Instances of this object can be used to process and ingest a grib file.
    """

    def __init__(self):
        # Get list of stations we're interested in, and store it so that we only call it once.
        self.stations = get_stations_synchronously()
        self.padf_transform = None
        self.raster_to_geo_transformer = None
        self.geo_to_raster_transformer = None
        self.prediction_model: PredictionModel = None

    def yield_data_for_stations(self, raster_band: gdal.Dataset):
        """ Given a list of stations, and a gdal dataset, yield relevant data
        """
        for station in self.stations:
            longitude = station.long
            latitude = station.lat

            x_coordinate, y_coordinate = calculate_raster_coordinate(
                longitude, latitude, self.padf_transform, self.geo_to_raster_transformer)

            if 0 <= x_coordinate < raster_band.XSize and 0 <= y_coordinate < raster_band.YSize:
                points, values = get_surrounding_grid(
                    raster_band, x_coordinate, y_coordinate)
            else:
                logger.warning('coordinate not in raster - %s', station)
                continue

            yield (points, values)

    def yield_uv_wind_data_for_stations(self, u_raster_band: gdal.Dataset, v_raster_band: gdal.Dataset, variable: str):
        """ Given a list of stations and 2 gdal datasets (one for u-component of wind, one for v-component
        of wind), yield relevant data 
        """
        for station in self.stations:
            longitude = station.long
            latitude = station.lat

            x_coordinate, y_coordinate = calculate_raster_coordinate(
                longitude, latitude, self.padf_transform, self.geo_to_raster_transformer)

            if 0 <= x_coordinate < u_raster_band.XSize and 0 <= x_coordinate < v_raster_band.XSize and\
                    0 <= y_coordinate < u_raster_band.YSize and 0 <= y_coordinate < v_raster_band.YSize:
                u_points, u_values = get_surrounding_grid(u_raster_band, x_coordinate, y_coordinate)
                v_points, v_values = get_surrounding_grid(v_raster_band, x_coordinate, y_coordinate)

                assert u_points == v_points

                zipped_uv_values = list(zip(u_values, v_values))

                if variable == 'wdir_tgl_10':
                    yield self.get_wind_dir_values(u_points, zipped_uv_values)
                elif variable == 'wind_tgl_10':
                    yield self.get_wind_speed_values(u_points, zipped_uv_values)
            else:
                logger.warning('coordinate not in u/v wind rasters - %s', station)

    def get_wind_dir_values(self, u_points: List[int], zipped_uv_values):
        """ Get calculated wind direction values for list of points and zipped u,v values """
        wind_dir_values = []
        for u, v in zipped_uv_values:
            wind_dir_values.append(calculate_wind_dir_from_u_v(u, v))
        return (u_points, wind_dir_values)

    def get_wind_speed_values(self, u_points: List[int], zipped_uv_values):
        """ Get calculated wind speed values for list of points and zipped u,v values """
        wind_speed_values = []
        for u, v in zipped_uv_values:
            wind_speed_values.append(calculate_wind_speed_from_u_v(u, v))
        return (u_points, wind_speed_values)

    def store_bounding_values(self,
                              points,
                              values,
                              preduction_model_run: PredictionModelRunTimestamp,
                              grib_info: ModelRunInfo,
                              session: Session):
        """ Store the values around the area of interest.
        """
        # Convert points to geographic coordinates:
        geographic_points = []
        for point in points:
            geographic_points.append(
                calculate_geographic_coordinate(point, self.padf_transform, self.raster_to_geo_transformer))
        # Get the grid subset, i.e. the relevant bounding area for this particular model.
        grid_subset = get_or_create_grid_subset(
            session, self.prediction_model, geographic_points)

        # Load the record if it exists.
        prediction = session.query(ModelRunGridSubsetPrediction).\
            filter(
                ModelRunGridSubsetPrediction.prediction_model_run_timestamp_id == preduction_model_run.id).\
            filter(ModelRunGridSubsetPrediction.prediction_timestamp == grib_info.prediction_timestamp).\
            filter(ModelRunGridSubsetPrediction.prediction_model_grid_subset_id ==
                   grid_subset.id).first()
        if not prediction:
            # Record doesn't exist, so we create it.
            prediction = ModelRunGridSubsetPrediction()
            prediction.prediction_model_run_timestamp_id = preduction_model_run.id
            prediction.prediction_timestamp = grib_info.prediction_timestamp
            prediction.prediction_model_grid_subset_id = grid_subset.id

        setattr(prediction, grib_info.variable_name.lower(), array(values))
        session.add(prediction)
        session.commit()

    def process_env_can_grib_file(self, session: Session, dataset, grib_info: ModelRunInfo,
                                  prediction_run: PredictionModelRunTimestamp):
        # for GDPS, RDPS, HRDPS models, always only ever 1 raster band in the dataset
        raster_band = dataset.GetRasterBand(1)
        # Iterate through stations:
        for (points, values) in self.yield_data_for_stations(raster_band):
            self.store_bounding_values(
                points, values, prediction_run, grib_info, session)

    def get_raster_bands(self, dataset, grib_info: ModelRunInfo):
        """ Returns raster bands of dataset for temperature, RH, U/V wind components, and 
        accumulated precip, depending on which interval of the model run we're analyzing. """
        # model_run_intervals is the number of hours difference between the prediction_timestamp and the
        # model_run_timestamp.
        # Need to know this to know which raster band ID we should use for GFS
        # grib files. Also, there won't be an accumulated precip band for the 000 interval.
        model_run_interval = (grib_info.prediction_timestamp -
                              grib_info.model_run_timestamp).total_seconds() / (60 * 60)
        if model_run_interval == 0:
            tmp_raster_band = dataset.GetRasterBand(GFS_000_HOURS_RASTER_BANDS.get('tmp_tgl_2'))
            rh_raster_band = dataset.GetRasterBand(GFS_000_HOURS_RASTER_BANDS.get('rh_tgl_2'))
            u_wind_raster_band = dataset.GetRasterBand(GFS_000_HOURS_RASTER_BANDS.get('u_comp_wind_10m'))
            v_wind_raster_band = dataset.GetRasterBand(GFS_000_HOURS_RASTER_BANDS.get('v_comp_wind_10m'))
            precip_raster_band = None
        else:
            tmp_raster_band = dataset.GetRasterBand(GFS_003_HOURS_RASTER_BANDS.get('tmp_tgl_2'))
            rh_raster_band = dataset.GetRasterBand(GFS_003_HOURS_RASTER_BANDS.get('rh_tgl_2'))
            u_wind_raster_band = dataset.GetRasterBand(GFS_003_HOURS_RASTER_BANDS.get('u_comp_wind_10m'))
            v_wind_raster_band = dataset.GetRasterBand(GFS_003_HOURS_RASTER_BANDS.get('v_comp_wind_10m'))
            precip_raster_band = dataset.GetRasterBand(GFS_003_HOURS_RASTER_BANDS.get('apcp_sfc_0'))

        return (tmp_raster_band, rh_raster_band, u_wind_raster_band, v_wind_raster_band, precip_raster_band)

    def process_noaa_grib_file(self, session: Session, dataset, grib_info: ModelRunInfo,
                               prediction_run: PredictionModelRunTimestamp):
        tmp_raster_band, rh_raster_band, u_wind_raster_band, v_wind_raster_band, precip_raster_band = self.get_raster_bands(
            dataset, grib_info)

        for (tmp_points, tmp_values) in self.yield_data_for_stations(tmp_raster_band):
            grib_info.variable_name = 'tmp_tgl_2'
            self.store_bounding_values(tmp_points, tmp_values, prediction_run, grib_info, session)
        for (rh_points, rh_values) in self.yield_data_for_stations(rh_raster_band):
            grib_info.variable_name = 'rh_tgl_2'
            self.store_bounding_values(rh_points, rh_values, prediction_run, grib_info, session)
        if precip_raster_band:
            for (apcp_points, apcp_values) in self.yield_data_for_stations(precip_raster_band):
                grib_info.variable_name = 'apcp_sfc_0'
                self.store_bounding_values(apcp_points, apcp_values, prediction_run, grib_info, session)
        for wdir_points, wdir_values in self.yield_uv_wind_data_for_stations(u_wind_raster_band, v_wind_raster_band, 'wdir_tgl_10'):
            grib_info.variable_name = 'wdir_tgl_10'
            self.store_bounding_values(wdir_points, wdir_values, prediction_run, grib_info, session)
        for (wind_points, wind_values) in self.yield_uv_wind_data_for_stations(u_wind_raster_band, v_wind_raster_band, 'wind_tgl_10'):
            grib_info.variable_name = 'wind_tgl_10'
            self.store_bounding_values(wind_points, wind_values, prediction_run, grib_info, session)

    def process_grib_file(self, filename, grib_info: ModelRunInfo, session: Session):
        """ Process a grib file, extracting and storing relevant information. """
        logger.info('processing %s', filename)
        # Open grib file
        dataset = open_grib(filename)
        # Ensure that grib file uses EPSG:4269 (NAD83) coordinate system
        # (this step is included because HRDPS grib files are in another coordinate system)
        wkt = dataset.GetProjection()
        crs = CRS.from_string(wkt)
        self.raster_to_geo_transformer = get_transformer(crs, NAD83_CRS)
        self.geo_to_raster_transformer = get_transformer(NAD83_CRS, crs)

        self.padf_transform = get_dataset_geometry(filename)
        # get the model (.e.g. GPDS/RDPS latlon24x.24):
        self.prediction_model = get_prediction_model(
            session, grib_info.model_enum, grib_info.projection)
        if not self.prediction_model:
            raise PredictionModelNotFound(
                'Could not find this prediction model in the database',
                grib_info.model_enum, grib_info.projection)

        # get the model run (e.g. GDPS latlon24x.24 for 2020 07 07 12h00):
        prediction_run = get_or_create_prediction_run(
            session, self.prediction_model, grib_info.model_run_timestamp)

        if self.prediction_model.abbreviation in ['GDPS', 'RDPS', 'HRDPS']:
            self.process_env_can_grib_file(session, dataset, grib_info, prediction_run)
        elif self.prediction_model.abbreviation == 'GFS':
            self.process_noaa_grib_file(session, dataset, grib_info, prediction_run)
