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
import app.db.database
from app.wildfire_one import _get_stations_local
from app.db.models import (
    PredictionModel, PredictionModelRun, ModelRunGridSubsetPrediction)
from app.db.crud import get_prediction_model, get_or_create_prediction_run, get_or_create_grid_subset


logger = logging.getLogger(__name__)


class ForecastModelNotFound(Exception):
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
        self.forecast_timestamp = None
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


def calculate_raster_coordinate(longitude: float, latitude: float, origin: List[int], pixel: List[int]):
    """ From a given longitude and latitude, calculate the raster coordinate corresponding to the
    top left point of the grid surrounding the given geographic coordinate.
    """
    delta_x = longitude - origin[0]
    delta_y = latitude - origin[1]
    x_coordinate = delta_x / pixel[0]
    y_coordinate = delta_y / pixel[1]
    return math.floor(x_coordinate), math.floor(y_coordinate)


def calculate_geographic_coordinate(point: List[int], origin: List[float], pixel: List[float]) -> List[float]:
    """ Calculate the geographic coordinates for a given points """
    x_coordinate = origin[0] + point[0] * pixel[0]
    y_coordinate = origin[1] + point[1] * pixel[1]
    return (x_coordinate, y_coordinate)


def open_grib(filename: str) -> gdal.Dataset:
    """ Open grib file """
    return gdal.Open(filename, gdal.GA_ReadOnly)


def get_dataset_geometry(dataset: gdal.Dataset) -> (List[int], List[int]):
    """ Get the geometry info (origin and pixel size) of the dataset.
    """
    geotransform = dataset.GetGeoTransform()
    # Upper left corner:
    origin = (geotransform[0], geotransform[3])
    # Pixel width and height:
    pixel = (geotransform[1], geotransform[5])
    return origin, pixel


class GribFileProcessor():
    """ Instances of this object can be used to process and ingest a grib file.
    """

    def __init__(self):
        # Get list of stations we're interested in, and store it so that we only call it once.
        self.stations = _get_stations_local()
        self.session = app.db.database.get_session()
        self.origin = None
        self.pixel = None
        self.prediction_model = None

    def get_prediction_model(self, grib_info: ModelRunInfo) -> PredictionModel:
        """ Get the prediction model, raising an exception if not found """
        prediction_model = get_prediction_model(
            self.session, grib_info.model_abbreviation, grib_info.projection)
        if not prediction_model:
            raise ForecastModelNotFound(
                'Could not find this forecast model in the database',
                grib_info.model_abbreviation, grib_info.projection)
        return prediction_model

    def yield_data_for_stations(self, raster_band):
        """ Given a list of stations, and a gdal dataset, yield relevant data
        """
        for station in self.stations:
            longitude = float(station['long'])
            latitude = float(station['lat'])
            x_coordinate, y_coordinate = calculate_raster_coordinate(
                longitude, latitude, self.origin, self.pixel)

            points, values = get_surrounding_grid(
                raster_band, x_coordinate, y_coordinate)

            yield (points, values)

    def store_bounding_values(self, points, values, preduction_model_run: PredictionModelRun,
                              grib_info: ModelRunInfo):
        """ Store the values around the area of interest.
        """
        # Convert points to geographic coordinates:
        geographic_points = []
        for point in points:
            geographic_points.append(
                calculate_geographic_coordinate(point, self.origin, self.pixel))

        # Get the grid subset, i.e. the relevant bounding area for this particular model.
        grid_subset = get_or_create_grid_subset(
            self.session, self.prediction_model, geographic_points)

        # Load the record if it exists.
        # pylint: disable=no-member
        prediction = self.session.query(ModelRunGridSubsetPrediction).\
            filter(ModelRunGridSubsetPrediction.prediction_model_run_id == preduction_model_run.id).\
            filter(ModelRunGridSubsetPrediction.prediction_timestamp == grib_info.forecast_timestamp).\
            filter(ModelRunGridSubsetPrediction.prediction_model_grid_subset_id ==
                   grid_subset.id).first()
        if not prediction:
            # Record doesn't exist, so we create it.
            prediction = ModelRunGridSubsetPrediction()
            prediction.prediction_model_run_id = preduction_model_run.id
            prediction.prediction_timestamp = grib_info.forecast_timestamp
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
            self.origin, self.pixel = get_dataset_geometry(dataset)

            # get the model (.e.g. GPDS/RDPS latlon24x.24):
            self.prediction_model = self.get_prediction_model(grib_info)
            # get the model run (e.g. GDPS latlon24x.24 for 2020 07 07 12h00):
            prediction_run = get_or_create_prediction_run(
                self.session, self.prediction_model, grib_info.model_run_timestamp)

            raster_band = dataset.GetRasterBand(1)

            # Iterate through stations:
            for (points, values) in self.yield_data_for_stations(raster_band):
                self.store_bounding_values(
                    points, values, prediction_run, grib_info)
        except sqlalchemy.exc.OperationalError:
            # Sometimes this exception is thrown with a "server closed the connection unexpectedly" error.
            # This could happen due to the connection being closed.
            if self.session.is_disconnect():
                logger.error("Database disconnected!")
                # Try to re-connect, so that subsequent calls to this function may succeed.
                # NOTE: I'm not sure if this will solve the problem!
                self.session = app.db.database.get_session()
                raise DatabaseException('Database disconnection')
            # Re-throw the exception.
            raise
