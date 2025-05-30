"""Read a grib file, and store values relevant to weather stations in database."""

from datetime import datetime
import math
import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from osgeo import gdal
from pyproj import CRS, Transformer
from affine import Affine
import numpy as np
from wps_shared.geospatial.geospatial import NAD83_CRS, get_dataset_transform, get_transformer
from wps_shared.stations import get_stations_synchronously
from wps_shared.db.models.weather_models import ModelRunPrediction, PredictionModel, PredictionModelRunTimestamp
from wps_shared.db.crud.weather_models import get_prediction_model, get_or_create_prediction_run
from wps_shared.weather_models import ModelEnum, ProjectionEnum
from wps_jobs.weather_model_jobs.utils.wind_direction_utils import calculate_wind_dir_from_u_v, calculate_wind_speed_from_u_v

logger = logging.getLogger(__name__)

GFS_000_HOURS_RASTER_BANDS = {"tmp_tgl_2": 2, "rh_tgl_2": 3, "u_comp_wind_10m": 4, "v_comp_wind_10m": 5}
GFS_003_HOURS_RASTER_BANDS = {"tmp_tgl_2": 2, "rh_tgl_2": 3, "u_comp_wind_10m": 4, "v_comp_wind_10m": 5, "apcp_sfc_0": 6, "cumulative_apcp_sfc_0": 7}


class PredictionModelNotFound(Exception):
    """Exception raised when specified model cannot be found in database."""


class DatabaseException(Exception):
    """Exception raised to to database related issue."""


class ModelRunInfo:
    """Information relation to a particular model run"""

    def __init__(self, model_enum=None, projection=None, model_run_timestamp=None, prediction_timestamp=None, variable_name=None):
        self.model_enum: Optional[ModelEnum] = model_enum
        self.projection: Optional[ProjectionEnum] = projection
        self.model_run_timestamp: Optional[datetime] = model_run_timestamp
        self.prediction_timestamp: Optional[datetime] = prediction_timestamp
        self.variable_name: Optional[str] = variable_name


def calculate_raster_coordinate(longitude: float, latitude: float, transform: Affine, transformer: Transformer):
    """From a given longitude and latitude, calculate the raster coordinate corresponding to the
    top left point of the grid surrounding the given geographic coordinate.
    """
    # Because not all model types use EPSG:4269 projection, we first convert longitude and latitude
    # to whichever projection and coordinate system the grib file is using
    raster_long, raster_lat = transformer.transform(longitude, latitude)
    reverse = ~transform
    i_index, j_index = reverse * (raster_long, raster_lat)
    return (math.floor(i_index), math.floor(j_index))


def convert_mps_to_kph(value: float):
    """Convert a value from metres per second to kilometres per hour."""
    return value / 1000 * 3600


def convert_kelvin_to_celsius(value: float):
    """Convert a value from kelvin to celsius."""
    return value - 273.15


def calculate_relative_humidity(temp: float, dew_temp: float) -> float:
    """
    Calculate relative humidity (RH) from air temperature and dew point temperature.

    :param temp: Air temperature in Kelvin.
    :param dew_temp: Dew point temperature in Kelvin.
    :return: Relative humidity
    """
    # Convert temperature and dew point from Kelvin to Celsius
    temp_c = convert_kelvin_to_celsius(temp)
    dew_temp_c = convert_kelvin_to_celsius(dew_temp)

    rh = 100 * (np.exp((17.625 * dew_temp_c) / (dew_temp_c + 243.04)) / np.exp((17.625 * temp_c) / (temp_c + 243.04)))

    return rh


class GribFileProcessor:
    """Instances of this object can be used to process and ingest a grib file."""

    def __init__(self, padf_transform=None, raster_to_geo_transformer=None, geo_to_raster_transformer=None):
        # Get list of stations we're interested in, and store it so that we only call it once.
        self.stations = get_stations_synchronously()
        self.padf_transform = padf_transform
        self.raster_to_geo_transformer = raster_to_geo_transformer
        self.geo_to_raster_transformer = geo_to_raster_transformer
        self.prediction_model: Optional[PredictionModel] = None

    def yield_value_for_stations(self, raster_band: gdal.Dataset):
        """Given a list of stations, and a gdal dataset, yield relevant data value"""
        for station in self.stations:
            longitude = station.long
            latitude = station.lat

            x_coordinate, y_coordinate = calculate_raster_coordinate(longitude, latitude, self.padf_transform, self.geo_to_raster_transformer)

            if 0 <= x_coordinate < raster_band.XSize and 0 <= y_coordinate < raster_band.YSize:
                value = raster_band.ReadAsArray(x_coordinate, y_coordinate, 1, 1)[0, 0]
            else:
                logger.warning("coordinate not in raster - %s", station)
                continue

            yield (station, value)

    def yield_uv_wind_data_for_stations(self, u_raster_band: gdal.Dataset, v_raster_band: gdal.Dataset, variable: str):
        """Given a list of stations and 2 gdal datasets (one for u-component of wind, one for v-component
        of wind), yield relevant data
        """
        for station in self.stations:
            longitude = station.long
            latitude = station.lat

            x_coordinate, y_coordinate = calculate_raster_coordinate(longitude, latitude, self.padf_transform, self.geo_to_raster_transformer)

            if (
                0 <= x_coordinate < u_raster_band.XSize
                and 0 <= x_coordinate < v_raster_band.XSize
                and 0 <= y_coordinate < u_raster_band.YSize
                and 0 <= y_coordinate < v_raster_band.YSize
            ):
                u_value = u_raster_band.ReadAsArray(x_coordinate, y_coordinate, 1, 1)[0, 0]
                v_value = v_raster_band.ReadAsArray(x_coordinate, y_coordinate, 1, 1)[0, 0]

                if variable == "wdir_tgl_10":
                    yield (station, calculate_wind_dir_from_u_v(u_value, v_value))
                elif variable == "wind_tgl_10":
                    metres_per_second_speed = calculate_wind_speed_from_u_v(u_value, v_value)
                    kilometres_per_hour_speed = convert_mps_to_kph(metres_per_second_speed)
                    yield (station, kilometres_per_hour_speed)
            else:
                logger.warning("coordinate not in u/v wind rasters - %s", station)

    def get_wind_dir_values(self, u_points: List[int], zipped_uv_values):
        """Get calculated wind direction values for list of points and zipped u,v values"""
        wind_dir_values = []
        for u, v in zipped_uv_values:
            wind_dir_values.append(calculate_wind_dir_from_u_v(u, v))
        return (u_points, wind_dir_values)

    def get_wind_speed_values(self, u_points: List[int], zipped_uv_values):
        """Get calculated wind speed values in kilometres per hour for a list of points
        and zipped u,v values"""
        wind_speed_values = []
        for u, v in zipped_uv_values:
            metres_per_second_speed = calculate_wind_speed_from_u_v(u, v)
            kilometres_per_hour_speed = convert_mps_to_kph(metres_per_second_speed)
            wind_speed_values.append(kilometres_per_hour_speed)
        return (u_points, wind_speed_values)

    def get_variable_name(self, grib_info: ModelRunInfo) -> str:
        """Return the name of the weather variable as it is used in our database,
        depending on which type of model is being processed"""
        variable_name = ""
        # March 2023: variable names used by Env.Can. for HRDPS model are no longer consistent
        # with the names used for RDPS and GDPS models, or with our database table. Quick and dirty
        # fix is to manually change the variable names as below
        if grib_info.model_enum == ModelEnum.HRDPS:
            if grib_info.variable_name == "TMP_AGL-2m":
                variable_name = "tmp_tgl_2"
            elif grib_info.variable_name == "RH_AGL-2m":
                variable_name = "rh_tgl_2"
            elif grib_info.variable_name == "WDIR_AGL-10m":
                variable_name = "wdir_tgl_10"
            elif grib_info.variable_name == "WIND_AGL-10m":
                variable_name = "wind_tgl_10"
            elif grib_info.variable_name == "APCP_Sfc":
                variable_name = "apcp_sfc_0"
        else:
            variable_name = grib_info.variable_name.lower()

        return variable_name

    def store_prediction_value(self, station_code: int, value: float, prediction_model_run: PredictionModelRunTimestamp, grib_info: ModelRunInfo, session: Session):
        """Store the values around the area of interest."""
        # Load the record if it exists.
        prediction = (
            session.query(ModelRunPrediction)
            .filter(ModelRunPrediction.prediction_model_run_timestamp_id == prediction_model_run.id)
            .filter(ModelRunPrediction.prediction_timestamp == grib_info.prediction_timestamp)
            .filter(ModelRunPrediction.station_code == station_code)
            .first()
        )
        if not prediction:
            # Record doesn't exist, so we create it.
            prediction = ModelRunPrediction()
            prediction.prediction_model_run_timestamp_id = prediction_model_run.id
            prediction.prediction_timestamp = grib_info.prediction_timestamp
            prediction.station_code = station_code

        variable_name = self.get_variable_name(grib_info)
        value = value.item() if isinstance(value, np.float64) else value
        setattr(prediction, variable_name, value)
        session.add(prediction)
        session.commit()

    def process_env_can_grib_file(self, session: Session, dataset, grib_info: ModelRunInfo, prediction_run: PredictionModelRunTimestamp):
        # for GDPS, RDPS, HRDPS models, always only ever 1 raster band in the dataset
        raster_band = dataset.GetRasterBand(1)
        # Iterate through stations:
        for station, value in self.yield_value_for_stations(raster_band):
            # Convert wind speed from metres per second to kilometres per hour for Environment Canada
            # models (NOAA models handled elswhere)
            if grib_info.variable_name.lower().startswith("wind_agl") or grib_info.variable_name.lower().startswith("wind_tgl"):
                value = convert_mps_to_kph(value)

            self.store_prediction_value(station.code, value, prediction_run, grib_info, session)

    def get_raster_bands(self, dataset, grib_info: ModelRunInfo):
        """Returns raster bands of dataset for temperature, RH, U/V wind components, and
        accumulated precip, depending on which interval of the model run we're analyzing."""
        # model_run_intervals is the number of hours difference between the prediction_timestamp and the
        # model_run_timestamp.
        # Need to know this to know which raster band ID we should use for GFS
        # grib files. Also, there won't be an accumulated precip band for the 000 interval.
        model_run_interval = (grib_info.prediction_timestamp - grib_info.model_run_timestamp).total_seconds() / (60 * 60)
        if model_run_interval == 0:
            tmp_raster_band = dataset.GetRasterBand(GFS_000_HOURS_RASTER_BANDS.get("tmp_tgl_2"))
            rh_raster_band = dataset.GetRasterBand(GFS_000_HOURS_RASTER_BANDS.get("rh_tgl_2"))
            u_wind_raster_band = dataset.GetRasterBand(GFS_000_HOURS_RASTER_BANDS.get("u_comp_wind_10m"))
            v_wind_raster_band = dataset.GetRasterBand(GFS_000_HOURS_RASTER_BANDS.get("v_comp_wind_10m"))
            precip_raster_band = None
        else:
            tmp_raster_band = dataset.GetRasterBand(GFS_003_HOURS_RASTER_BANDS.get("tmp_tgl_2"))
            rh_raster_band = dataset.GetRasterBand(GFS_003_HOURS_RASTER_BANDS.get("rh_tgl_2"))
            u_wind_raster_band = dataset.GetRasterBand(GFS_003_HOURS_RASTER_BANDS.get("u_comp_wind_10m"))
            v_wind_raster_band = dataset.GetRasterBand(GFS_003_HOURS_RASTER_BANDS.get("v_comp_wind_10m"))
            precip_raster_band = dataset.GetRasterBand(GFS_003_HOURS_RASTER_BANDS.get("apcp_sfc_0"))

        # The GFS grib file has an extra band that contains cumulative precipitation
        if grib_info.model_enum == ModelEnum.GFS:
            precip_raster_band = dataset.GetRasterBand(GFS_003_HOURS_RASTER_BANDS.get("cumulative_apcp_sfc_0"))

        return (tmp_raster_band, rh_raster_band, u_wind_raster_band, v_wind_raster_band, precip_raster_band)

    def process_noaa_grib_file(self, session: Session, dataset, grib_info: ModelRunInfo, prediction_run: PredictionModelRunTimestamp):
        tmp_raster_band, rh_raster_band, u_wind_raster_band, v_wind_raster_band, precip_raster_band = self.get_raster_bands(dataset, grib_info)

        for station, tmp_value in self.yield_value_for_stations(tmp_raster_band):
            grib_info.variable_name = "tmp_tgl_2"
            self.store_prediction_value(station.code, tmp_value, prediction_run, grib_info, session)
        for station, rh_value in self.yield_value_for_stations(rh_raster_band):
            grib_info.variable_name = "rh_tgl_2"
            self.store_prediction_value(station.code, rh_value, prediction_run, grib_info, session)
        if precip_raster_band:
            for station, apcp_value in self.yield_value_for_stations(precip_raster_band):
                grib_info.variable_name = "apcp_sfc_0"
                self.store_prediction_value(station.code, apcp_value, prediction_run, grib_info, session)
        for station, wdir_value in self.yield_uv_wind_data_for_stations(u_wind_raster_band, v_wind_raster_band, "wdir_tgl_10"):
            grib_info.variable_name = "wdir_tgl_10"
            self.store_prediction_value(station.code, wdir_value, prediction_run, grib_info, session)
        for station, wind_value in self.yield_uv_wind_data_for_stations(u_wind_raster_band, v_wind_raster_band, "wind_tgl_10"):
            grib_info.variable_name = "wind_tgl_10"
            self.store_prediction_value(station.code, wind_value, prediction_run, grib_info, session)

    def process_grib_file(self, filename, grib_info: ModelRunInfo, session: Session):
        """Process a grib file, extracting and storing relevant information."""
        logger.info("processing %s", filename)
        # Open grib file
        dataset = gdal.Open(filename, gdal.GA_ReadOnly)
        # Ensure that grib file uses EPSG:4269 (NAD83) coordinate system
        # (this step is included because HRDPS grib files are in another coordinate system)
        wkt = dataset.GetProjection()
        crs = CRS.from_string(wkt)
        self.raster_to_geo_transformer = get_transformer(crs, NAD83_CRS)
        self.geo_to_raster_transformer = get_transformer(NAD83_CRS, crs)

        self.padf_transform = get_dataset_transform(filename)
        # get the model (.e.g. GPDS/RDPS latlon24x.24):
        self.prediction_model = get_prediction_model(session, grib_info.model_enum, grib_info.projection)
        if not self.prediction_model:
            raise PredictionModelNotFound("Could not find this prediction model in the database", grib_info.model_enum, grib_info.projection)

        # get the model run (e.g. GDPS latlon24x.24 for 2020 07 07 12h00):
        prediction_run = get_or_create_prediction_run(session, self.prediction_model, grib_info.model_run_timestamp)

        if self.prediction_model.abbreviation in ["GDPS", "RDPS", "HRDPS"]:
            self.process_env_can_grib_file(session, dataset, grib_info, prediction_run)
        elif self.prediction_model.abbreviation in ["GFS", "NAM"]:
            self.process_noaa_grib_file(session, dataset, grib_info, prediction_run)
        dataset = None
