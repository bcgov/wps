import xarray
import pandas as pd
import xarray as xr
from herbie import Herbie
from wps_shared.db.models.weather_models import ModelRunPrediction
from weather_model_jobs import ModelRunInfo, ModelRunProcessResult
from weather_model_jobs.utils.process_grib import convert_mps_to_kph, convert_kelvin_to_celsius, calculate_relative_humidity

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


class ECMWFModelProcessor:
    model_run_info: ModelRunInfo
    data: xarray.Dataset

    def __init__(self, working_directory: str, geo_to_raster_transformer=None):
        self.geo_to_raster_transformer = geo_to_raster_transformer
        self.working_dir = working_directory

    def process_grib_data(
        self,
        herbie_instance: Herbie,
        grib_info: ModelRunInfo,
        stations_df: pd.DataFrame,
    ) -> ModelRunProcessResult:
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
        station_data: xarray.Dataset = weather_ds.herbie.pick_points(stations_df, method="nearest")
        station_data = station_data.swap_dims({"point": "point_code"})

        # calculate rh, convert wind, temp, and precip units
        station_data[RH_FIELD] = xr.apply_ufunc(calculate_relative_humidity, station_data[TEMP_FIELD], station_data[DEW_FIELD])
        station_data[WS_FIELD] = xr.apply_ufunc(convert_mps_to_kph, station_data[WS_FIELD])
        station_data[TEMP_FIELD] = xr.apply_ufunc(convert_kelvin_to_celsius, station_data[TEMP_FIELD])
        station_data[PRECIP_FIELD] = station_data[PRECIP_FIELD] * 1000  # m to mm

        rename_dict = {
            TEMP_FIELD: ModelRunPrediction.tmp_tgl_2.name,
            RH_FIELD: ModelRunPrediction.rh_tgl_2.name,
            PRECIP_FIELD: ModelRunPrediction.apcp_sfc_0.name,
            WS_FIELD: ModelRunPrediction.wind_tgl_10.name,
            WDIR_FIELD: ModelRunPrediction.wdir_tgl_10.name,
        }
        station_data = station_data.rename(rename_dict)

        return ModelRunProcessResult(model_run_info=grib_info, url=herbie_instance.grib, data=station_data)
