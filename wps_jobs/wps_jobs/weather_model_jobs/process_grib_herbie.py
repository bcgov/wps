import os
from typing import List, Optional

import numpy as np
import pandas as pd
import xarray as xr
from herbie import Herbie
from osgeo import gdal
from pyproj import CRS

from wps_jobs.weather_model_jobs import ModelEnum, ProjectionEnum
from wps_shared.geospatial.geospatial import NAD83_CRS, get_transformer
from wps_shared.schemas.stations import WeatherStation
from wps_jobs.weather_model_jobs import ModelRunInfo, ModelRunProcessResult
from wps_jobs.weather_model_jobs.utils.process_grib import convert_mps_to_kph, convert_kelvin_to_celsius


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


def calculate_relative_humidity(temp: float, dew_temp: float) -> float:
    """
    Calculate relative humidity (RH) from air temperature and dew point temperature.

    :param temp: Air temperature in Kelvin.
    :param dew_temp: Dew point temperature in Kelvin.
    :return: Relative humidity
    """
    # Convert temperature and dew point from Kelvin to Celsius
    temp_c = convert_kelvin_to_celsius(temp)
    dew_temp_c = dew_temp - 273.15

    rh = 100 * (np.exp((17.625 * dew_temp_c) / (dew_temp_c + 243.04)) / np.exp((17.625 * temp_c) / (temp_c + 243.04)))

    return rh


class HerbieGribProcessor:
    def __init__(self, working_directory: str, geo_to_raster_transformer=None):
        self.geo_to_raster_transformer = geo_to_raster_transformer
        self.working_dir = working_directory

    def process_grib_file(self, herbie_instance: Herbie, grib_info: ModelRunInfo, stations: List[WeatherStation]) -> Optional[xr.Dataset]:
        if not self.geo_to_raster_transformer:
            self.set_transformer(herbie_instance)
        self.stations_df = self.get_stations_dataframe(stations)

        if grib_info.model_enum.value == "ECMWF":
            return self.process_ecmwf_grib_file(herbie_instance, grib_info)

    def process_ecmwf_grib_file(
        self,
        herbie_instance: Herbie,
        grib_info: ModelRunInfo,
    ) -> Optional[xr.Dataset]:
        weather_params = [TEMP, PRECIP, DEW_TEMP, WIND]

        # merge all necessary data into a single xarray dataset
        datasets = []
        for param in weather_params:
            if param == WIND:
                ds = herbie_instance.xarray(param, save_dir=self.working_dir).herbie.with_wind()
            else:
                ds = herbie_instance.xarray(param, save_dir=self.working_dir, remove_grib=True)
            datasets.append(ds)
        weather_ds = xr.merge(datasets, compat="override")

        # extract data for each station
        station_data = weather_ds.herbie.pick_points(self.stations_df, method="nearest")

        # calculate rh, convert wind, temp, and precip units
        station_data[RH_FIELD] = xr.apply_ufunc(calculate_relative_humidity, station_data[TEMP_FIELD], station_data[DEW_FIELD])
        station_data[WS_FIELD] = xr.apply_ufunc(convert_mps_to_kph, station_data[WS_FIELD])
        station_data[TEMP_FIELD] = xr.apply_ufunc(convert_kelvin_to_celsius, station_data[TEMP_FIELD])
        station_data[PRECIP_FIELD] = station_data[PRECIP_FIELD] * 1000  # m to mm

        return ModelRunProcessResult(model_run_info=grib_info, url=herbie_instance.grib, data=station_data)

    def get_stations_dataframe(self, stations: List[WeatherStation]):
        stations_df = pd.DataFrame([station.model_dump(include={"code", "name", "lat", "long"}) for station in stations]).rename(columns={"lat": "latitude", "long": "longitude"})

        stations_df[["longitude", "latitude"]] = stations_df.apply(
            lambda row: self.geo_to_raster_transformer.transform(row["longitude"], row["latitude"]),
            axis=1,
            result_type="expand",
        )
        return stations_df

    def set_transformer(self, herbie_instance: Herbie):
        grib = herbie_instance.download(TEMP, verbose=False, save_dir=self.working_dir)  # Any variable can be used to get the model projection
        dataset = gdal.Open(grib)

        wkt = dataset.GetProjection()
        crs = CRS.from_string(wkt)
        self.geo_to_raster_transformer = get_transformer(NAD83_CRS, crs)

        dataset = None
        os.remove(grib)
