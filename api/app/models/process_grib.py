""" Read a grib file, and store values relevant to weather stations in database.
"""

import math
import struct
import logging
import logging.config
from typing import List
from sqlalchemy.dialects.postgresql import array
import sqlalchemy.exc
import gdal
from pyproj import CRS, Transformer
import app.db.database
from app.stations import get_stations_synchronously
from app.db.models import (
    PredictionModel, PredictionModelRunTimestamp, ModelRunGridSubsetPrediction)
from app.db.crud import get_prediction_model, get_or_create_prediction_run, get_or_create_grid_subset


logger = logging.getLogger(__name__)


class PredictionModelNotFound(Exception):
    """ Exception raised when specified model cannot be found in database. """


class DatabaseException(Exception):
    """ Exception raised to to database related issue. """


class ModelRunInfo():
    """ Information relation to a particular model run
    """

    def __init__(self):
        self.model_abbreviation = None
        self.projection = None
        self.model_run_timestamp = None
        self.prediction_timestamp = None
        self.variable_name = None


def get_surrounding_grid(
        band: gdal.Dataset, x_index: int, y_index: int) -> (List[int], List[float]):
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
    scanline_two = band.ReadRaster(xoff=x_index, yoff=y_index+1, xsize=2, ysize=1,
                                   buf_xsize=2, buf_ysize=1, buf_type=gdal.GDT_Float32)
    row_two = struct.unpack('f' * 2, scanline_two)
    values.append(row_two[1])
    values.append(row_two[0])

    points = [[x_index, y_index], [x_index+1, y_index],
              [x_index+1, y_index+1], [x_index, y_index+1]]

    return points, values


def calculate_raster_coordinate(
        longitude: float,
        latitude: float,
        padf_transform: List[float],
        transformer: Transformer):
    """ From a given longitude and latitude, calculate the raster coordinate corresponding to the
    top left point of the grid surrounding the given geographic coordinate.
    """
    # Because not all model types use EPSG:4269 projection, we first convert longitude and latitude
    # to whichever projection and coordinate system the grib file is using
    raster_lat, raster_long = transformer.transform(latitude, longitude)

    logger.info('padf_transform in calculate_raster() is %s', padf_transform)

    # Calculate the j index for point i,j in the grib file
    numerator = padf_transform[1] * (raster_long - padf_transform[3]) - \
        padf_transform[4] * (raster_lat - padf_transform[0])
    denominator = padf_transform[1] * padf_transform[5] - \
        padf_transform[2] * padf_transform[4]
    j_index = math.floor(numerator/denominator)

    # Calculate the i index for point i,j in the grib file
    numerator = raster_lat - padf_transform[0] - j_index * padf_transform[2]
    denominator = padf_transform[1]
    i_index = math.floor(numerator/denominator)

    return (i_index, j_index)


def calculate_geographic_coordinate(
        point: List[int],
        padf_transform: List[float],
        transformer: Transformer):
    """ Calculate the geographic coordinates for a given points """
    x_coordinate = padf_transform[0] + point[0] * \
        padf_transform[1] + point[1]*padf_transform[2]
    y_coordinate = padf_transform[3] + point[0] * \
        padf_transform[4] + point[1]*padf_transform[5]

    lat, lon = transformer.transform(x_coordinate, y_coordinate)
    return (lon, lat)


def open_grib(filename: str) -> gdal.Dataset:
    """ Open grib file """
    return gdal.Open(filename, gdal.GA_ReadOnly)


def get_dataset_geometry(dataset: gdal.Dataset) -> (List[int], List[int]):
    """ Get the geometry info (origin and pixel size) of the dataset.
    """
    return dataset.GetGeoTransform()


class GribFileProcessor():
    """ Instances of this object can be used to process and ingest a grib file.
    """

    def __init__(self):
        # Get list of stations we're interested in, and store it so that we only call it once.
        self.stations = get_stations_synchronously()
        self.session = app.db.database.get_write_session()
        self.padf_transform = None
        self.raster_to_geo_transformer = None
        self.geo_to_raster_transformer = None
        self.prediction_model = None

    def get_prediction_model(self, grib_info: ModelRunInfo) -> PredictionModel:
        """ Get the prediction model, raising an exception if not found """
        prediction_model = get_prediction_model(
            self.session, grib_info.model_abbreviation, grib_info.projection)
        if not prediction_model:
            raise PredictionModelNotFound(
                'Could not find this prediction model in the database',
                grib_info.model_abbreviation, grib_info.projection)
        return prediction_model

    def yield_data_for_stations(self, raster_band):
        """ Given a list of stations, and a gdal dataset, yield relevant data
        """
        for station in self.stations:
            longitude = station.long
            latitude = station.lat
            x_coordinate, y_coordinate = calculate_raster_coordinate(
                longitude, latitude, self.padf_transform, self.geo_to_raster_transformer)

            points, values = get_surrounding_grid(
                raster_band, x_coordinate, y_coordinate)

            yield (points, values)

    def store_bounding_values(self, points, values, preduction_model_run: PredictionModelRunTimestamp,
                              grib_info: ModelRunInfo):
        """ Store the values around the area of interest.
        """
        # Convert points to geographic coordinates:
        geographic_points = []
        for point in points:
            geographic_points.append(
                calculate_geographic_coordinate(point, self.padf_transform, self.raster_to_geo_transformer))
        # Get the grid subset, i.e. the relevant bounding area for this particular model.
        grid_subset = get_or_create_grid_subset(
            self.session, self.prediction_model, geographic_points)

        # Load the record if it exists.
        # pylint: disable=no-member
        prediction = self.session.query(ModelRunGridSubsetPrediction).\
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
        self.session.add(prediction)
        self.session.commit()

    def process_grib_file(self, filename, grib_info: ModelRunInfo):
        """ Process a grib file, extracting and storing relevant information. """
        try:
            logger.info('processing %s', filename)
            # Open grib file
            dataset = open_grib(filename)
            # Ensure that grib file uses EPSG:4269 (NAD83) coordinate system
            # (this step is included because HRDPS grib files are in another coordinate system)
            wkt = dataset.GetProjection()
            crs = CRS.from_string(wkt)
            geo_crs = CRS('epsg:4269')
            self.raster_to_geo_transformer = Transformer.from_crs(crs, geo_crs)
            self.geo_to_raster_transformer = Transformer.from_crs(geo_crs, crs)

            self.padf_transform = get_dataset_geometry(dataset)
            # get the model (.e.g. GPDS/RDPS latlon24x.24):
            self.prediction_model = self.get_prediction_model(grib_info)

            # if the model type is GDPS (Global), we need to manually set the padTransform
            # with the x,y coordinates of origin reversed
            if self.prediction_model.abbreviation == 'GDPS':
                revised_transform = (
                    self.padf_transform[3],
                    self.padf_transform[5],
                    self.padf_transform[2],
                    self.padf_transform[0],
                    self.padf_transform[4],
                    self.padf_transform[1])
                dataset.SetGeoTransform(revised_transform)
                self.padf_transform = revised_transform
                logger.info('GDPS padf_transform set to %s. Dataset geotransform %s',
                            self.padf_transform, dataset.GetGeoTransform())

            # get the model run (e.g. GDPS latlon24x.24 for 2020 07 07 12h00):
            prediction_run = get_or_create_prediction_run(
                self.session, self.prediction_model, grib_info.model_run_timestamp)

            raster_band = dataset.GetRasterBand(1)

            # Iterate through stations:
            for (points, values) in self.yield_data_for_stations(raster_band):
                self.store_bounding_values(
                    points, values, prediction_run, grib_info)
        except sqlalchemy.exc.OperationalError as exception:
            # Sometimes this exception is thrown with a "server closed the connection unexpectedly" error.
            # This could happen due to the connection being closed.
            if self.session.is_disconnect():
                logger.error("Database disconnected!")
                # Try to re-connect, so that subsequent calls to this function may succeed.
                # NOTE: I'm not sure if this will solve the problem!
                self.session = app.db.database.get_read_session()
                raise DatabaseException(
                    'Database disconnection') from exception
            # Re-throw the exception.
            raise
