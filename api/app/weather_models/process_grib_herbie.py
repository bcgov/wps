import os

import numpy as np
import pandas as pd
import xarray as xr
from herbie import Herbie
from osgeo import gdal
from pyproj import CRS
from sqlalchemy.orm import Session

from app.db.crud.weather_models import get_or_create_prediction_run, get_prediction_model
from app.db.models.weather_models import (
    ModelRunPrediction,
    PredictionModel,
    PredictionModelRunTimestamp,
)
from app.geospatial import NAD83_CRS
from app.stations import get_stations_synchronously
from app.weather_models import ModelEnum
from app.weather_models.process_grib import ModelRunInfo, convert_mps_to_kph, get_transformer

gdal.UseExceptions()

# ECMWF regex search strings
TEMP = ":2t:"  # Temperature at 2 meters
DEW_TEMP = ":2d:"  # Dew point temperature at 2 meters, used to calculate RH
WIND = ":10[u|v]:"  # Wind components (u and v) at 10 meters.
PRECIP = ":tp:"  # Total precipitation

# ECMWF weather fields
TEMP_FIELD = "t2m"
WDIR_FIELD = "wdir10"
WS_FIELD = "si10"
PRECIP_FIELD = "tp"
DEW_FIELD = "d2m"
RH_FIELD = "rh"  # this is calculated by us

# ModelRunPrediction weather parameter fields
DB_WEATHER_FIELDS = {
    "temp": ModelRunPrediction.tmp_tgl_2.name,
    "rh": ModelRunPrediction.rh_tgl_2.name,
    "ws": ModelRunPrediction.wind_tgl_10.name,
    "wdir": ModelRunPrediction.wdir_tgl_10.name,
    "precip": ModelRunPrediction.apcp_sfc_0.name,
}


def calculate_relative_humidity(temp: xr.DataArray, dew_temp: xr.DataArray) -> xr.DataArray:
    """
    Calculate relative humidity (RH) from air temperature and dew point temperature.

    :param temp: Air temperature in Kelvin.
    :param dew_temp: Dew point temperature in Kelvin.
    :return: Relative humidity
    """
    if (temp < 0).any() or (dew_temp < 0).any():
        raise ValueError("Temperature and dew point must be in Kelvin and non-negative.")
    if (dew_temp > temp).any():
        raise ValueError("Dew point cannot exceed air temperature.")
    # Convert temperature and dew point from Kelvin to Celsius
    temp_c = temp - 273.15
    dew_temp_c = dew_temp - 273.15

    rh = 100 * (
        np.exp((17.625 * dew_temp_c) / (dew_temp_c + 243.04))
        / np.exp((17.625 * temp_c) / (temp_c + 243.04))
    )

    return rh


class HerbieGribProcessor:
    def __init__(self, working_directory: str, geo_to_raster_transformer=None):
        self.stations = get_stations_synchronously()
        self.geo_to_raster_transformer = geo_to_raster_transformer
        self.prediction_model: PredictionModel = None
        self.working_dir = working_directory

    def process_grib_file(
        self,
        herbie_instance: Herbie,
        grib_info: ModelRunInfo,
        prediction_run: PredictionModelRunTimestamp,
        session: Session,
    ):
        if not self.geo_to_raster_transformer:
            self.set_transformer(herbie_instance)
        self.stations_df = self.get_stations_dataframe()

        if grib_info.model_enum.value == "ECMWF":
            self.process_ecmwf_grib_file(session, herbie_instance, grib_info, prediction_run)

    def process_ecmwf_grib_file(
        self,
        session: Session,
        herbie_instance: Herbie,
        grib_info: ModelRunInfo,
        prediction_run: PredictionModelRunTimestamp,
    ):
        weather_params = [TEMP, PRECIP, DEW_TEMP, WIND]

        station_data = self.select_station_data(herbie_instance, self.stations_df, weather_params)

        # calculate rh, convert wind, temp, and precip units
        station_data[RH_FIELD] = xr.apply_ufunc(
            calculate_relative_humidity, station_data[TEMP_FIELD], station_data[DEW_FIELD]
        )
        station_data[WS_FIELD] = xr.apply_ufunc(convert_mps_to_kph, station_data[WS_FIELD])
        station_data[TEMP_FIELD] = station_data[TEMP_FIELD] - 273.15  # Kelvin to Celsius
        station_data[PRECIP_FIELD] = station_data[PRECIP_FIELD] * 1000  # m to mm

        # name variables according to ModelRunPrediction table
        renamed_station_data = self.get_variable_names(station_data, grib_info)

        self.store_prediction_values(renamed_station_data, prediction_run, grib_info, session)

    def select_station_data(
        self, herbie_instance: Herbie, stations: pd.DataFrame, weather_params: list[str]
    ) -> xr.Dataset:
        datasets = []

        for param in weather_params:
            if param == WIND:
                ds = herbie_instance.xarray(param, save_dir=self.working_dir).herbie.with_wind()
            else:
                ds = herbie_instance.xarray(param, save_dir=self.working_dir)
            datasets.append(ds)
        weather_ds = xr.merge(datasets, compat="override")

        # extract data for each station
        station_data = weather_ds.herbie.pick_points(stations, method="nearest")

        station_data = station_data.swap_dims({"point": "point_code"})

        return station_data

    def store_prediction_values(
        self,
        dataset: xr.Dataset,
        prediction_run: PredictionModelRunTimestamp,
        grib_info: ModelRunInfo,
        session: Session,
    ):
        for station in self.stations:
            prediction = (
                session.query(ModelRunPrediction)
                .filter(ModelRunPrediction.prediction_model_run_timestamp_id == prediction_run.id)
                .filter(ModelRunPrediction.prediction_timestamp == grib_info.prediction_timestamp)
                .filter(ModelRunPrediction.station_code == station.code)
                .first()
            )
            if not prediction:
                prediction = ModelRunPrediction()
                prediction.prediction_model_run_timestamp_id = prediction_run.id
                prediction.prediction_timestamp = grib_info.prediction_timestamp
                prediction.station_code = station.code

            station_data = dataset.sel(point_code=station.code)

            for field in DB_WEATHER_FIELDS.values():
                if field in station_data:
                    setattr(prediction, field, station_data[field].item())

            session.add(prediction)
        session.commit()

    def get_variable_names(self, dataset: xr.Dataset, grib_info: ModelRunInfo):
        if grib_info.model_enum == ModelEnum.ECMWF:
            rename_dict = {
                TEMP_FIELD: DB_WEATHER_FIELDS["temp"],
                RH_FIELD: DB_WEATHER_FIELDS["rh"],
                PRECIP_FIELD: DB_WEATHER_FIELDS["precip"],
                WS_FIELD: DB_WEATHER_FIELDS["ws"],
                WDIR_FIELD: DB_WEATHER_FIELDS["wdir"],
            }
            renamed_dataset = dataset.rename(rename_dict)
            return renamed_dataset

    def get_stations_dataframe(self):
        stations_df = pd.DataFrame(
            [
                station.model_dump(include={"code", "name", "lat", "long"})
                for station in self.stations
            ]
        ).rename(columns={"lat": "latitude", "long": "longitude"})

        stations_df[["longitude", "latitude"]] = stations_df.apply(
            lambda row: self.geo_to_raster_transformer.transform(row["longitude"], row["latitude"]),
            axis=1,
            result_type="expand",
        )
        return stations_df

    def set_transformer(self, herbie_instance: Herbie):
        grib = herbie_instance.download(
            TEMP, verbose=False, save_dir=self.working_dir
        )  # Any variable can be used to get the model projection
        dataset = gdal.Open(grib)

        wkt = dataset.GetProjection()
        crs = CRS.from_string(wkt)
        self.geo_to_raster_transformer = get_transformer(NAD83_CRS, crs)

        dataset = None
        os.remove(grib)
