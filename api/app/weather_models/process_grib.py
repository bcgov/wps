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
from app.geospatial import NAD83_CRS
from app.stations import get_stations_synchronously
from app.db.models import (
    PredictionModel, PredictionModelRunTimestamp, ModelRunGridSubsetPrediction)
from app.db.crud.weather_models import (
    get_prediction_model, get_or_create_prediction_run, get_or_create_grid_subset)
from app.weather_models import ModelEnum, ProjectionEnum


logger = logging.getLogger(__name__)


class PredictionModelNotFound(Exception):
    """ Exception raised when specified model cannot be found in database. """


class DatabaseException(Exception):
    """ Exception raised to to database related issue. """


class ModelRunInfo():
    """ Information relation to a particular model run
    """

    def __init__(self):
        self.model_enum: Optional[ModelEnum] = None
        self.projection: Optional[ProjectionEnum] = None
        self.model_run_timestamp: Optional[datetime] = None
        self.prediction_timestamp: Optional[datetime] = None
        self.variable_name: Optional[str] = None


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
    raster_long, raster_lat = transformer.transform(longitude, latitude)

    # Calculate the j index for point i,j in the grib file
    x_numerator = (raster_long - padf_transform[0] - raster_lat/padf_transform[5] *
                   padf_transform[2] + padf_transform[3] / padf_transform[5] *
                   padf_transform[2]) / padf_transform[1]

    y_numerator = (raster_lat - padf_transform[3] - raster_long/padf_transform[1] *
                   padf_transform[4] + padf_transform[0] / padf_transform[1] *
                   padf_transform[4]) / padf_transform[5]

    denominator = 1 - \
        padf_transform[4]/padf_transform[5]*padf_transform[2]/padf_transform[1]

    i_index = math.floor(x_numerator/denominator)
    j_index = math.floor(y_numerator/denominator)

    return (i_index, j_index)


def calculate_geographic_coordinate(
        point: Tuple[int],
        padf_transform: List[float],
        transformer: Transformer):
    """ Calculate the geographic coordinates for a given points """
    x_coordinate = padf_transform[0] + point[0] * \
        padf_transform[1] + point[1]*padf_transform[2]
    y_coordinate = padf_transform[3] + point[0] * \
        padf_transform[4] + point[1]*padf_transform[5]

    lon, lat = transformer.transform(x_coordinate, y_coordinate)
    return (lon, lat)


def open_grib(filename: str) -> gdal.Dataset:
    """ Open grib file """
    return gdal.Open(filename, gdal.GA_ReadOnly)


def get_dataset_geometry(dataset: gdal.Dataset) -> (List[int], List[int]):
    """ Get the geometry info (origin and pixel size) of the dataset.
    """
    return dataset.GetGeoTransform()


def get_transformer(crs_from, crs_to):
    """ Get an appropriate transformer - it's super important that always_xy=True
    is specified, otherwise the order in the CRS definition is honoured. """
    return Transformer.from_crs(crs_from, crs_to, always_xy=True)


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

    # pylint: disable=too-many-arguments
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
        # pylint: disable=no-member
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

        self.padf_transform = get_dataset_geometry(dataset)
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

        raster_band = dataset.GetRasterBand(1)

        # Iterate through stations:
        for (points, values) in self.yield_data_for_stations(raster_band):
            self.store_bounding_values(
                points, values, prediction_run, grib_info, session)
