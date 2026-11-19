import pandas as pd
import xarray
import xarray as xr
from herbie import Herbie
from pyproj import Transformer
from weather_model_jobs import ModelRunInfo, ModelRunProcessResult
from weather_model_jobs.utils.process_grib import (
    calculate_relative_humidity,
    convert_kelvin_to_celsius,
    convert_mps_to_kph,
)
from wps_shared.db.models.weather_models import ModelRunPrediction
from wps_shared.geospatial.bounds import (
    BC_MAX_LATITUDE,
    BC_MAX_LONGITUDE,
    BC_MIN_LATITUDE,
    BC_MIN_LONGITUDE,
)
from wps_shared.schemas.stations import WeatherStation

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


def crop_to_bc(dataset: xr.Dataset) -> xr.Dataset:
    """Return an independent copy of the grid within the buffered BC bounds.

    Normalize longitudes and round coordinates only for boundary comparisons,
    so floating point errors do not exclude points on the bounds. Preserve
    the original coordinates and weather values in the returned dataset.

    Raise ValueError if the crop contains no latitude or longitude points.
    """
    latitude = dataset.latitude.round(8)
    longitude = ((dataset.longitude + 180) % 360 - 180).round(8)
    cropped = dataset.isel(
        latitude=(latitude >= BC_MIN_LATITUDE) & (latitude <= BC_MAX_LATITUDE),
        longitude=(longitude >= BC_MIN_LONGITUDE) & (longitude <= BC_MAX_LONGITUDE),
    )
    if not cropped.sizes["latitude"] or not cropped.sizes["longitude"]:
        raise ValueError("ECMWF dataset has no grid points within BC crop bounds")
    return cropped


def get_stations_dataframe(
    transformer: Transformer, stations: list[WeatherStation]
) -> pd.DataFrame:
    """Transform station coordinates and return Herbie's station table.

    Columns are code, name, latitude, and longitude.
    """
    stations_df = pd.DataFrame(
        [station.model_dump(include={"code", "name", "lat", "long"}) for station in stations]
    ).rename(columns={"lat": "latitude", "long": "longitude"})

    stations_df[["longitude", "latitude"]] = stations_df.apply(
        lambda row: transformer.transform(row["longitude"], row["latitude"]),
        axis=1,
        result_type="expand",
    )
    return stations_df


def sample_station_points(dataset: xr.Dataset, stations_df: pd.DataFrame) -> xr.Dataset:
    """Return each station's nearest ECMWF cell, indexed by point_code.

    Sample the supplied cropped dataset using Herbie's nearest point lookup.
    """
    selected = dataset.herbie.pick_points(stations_df, method="nearest", use_cached_tree=False)
    return selected.swap_dims({"point": "point_code"})


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
            ds = crop_to_bc(
                herbie_instance.xarray(param, save_dir=self.working_dir, remove_grib=True)
            )
            datasets.append(ds)
        weather_ds = xr.merge(datasets, compat="override")

        # extract data for each station
        station_data = sample_station_points(weather_ds, stations_df).herbie.with_wind()

        # calculate rh, convert wind, temp, and precip units
        station_data[RH_FIELD] = xr.apply_ufunc(
            calculate_relative_humidity, station_data[TEMP_FIELD], station_data[DEW_FIELD]
        )
        station_data[WS_FIELD] = xr.apply_ufunc(convert_mps_to_kph, station_data[WS_FIELD])
        station_data[TEMP_FIELD] = xr.apply_ufunc(
            convert_kelvin_to_celsius, station_data[TEMP_FIELD]
        )
        station_data[PRECIP_FIELD] = station_data[PRECIP_FIELD] * 1000  # m to mm

        rename_dict = {
            TEMP_FIELD: ModelRunPrediction.tmp_tgl_2.name,
            RH_FIELD: ModelRunPrediction.rh_tgl_2.name,
            PRECIP_FIELD: ModelRunPrediction.apcp_sfc_0.name,
            WS_FIELD: ModelRunPrediction.wind_tgl_10.name,
            WDIR_FIELD: ModelRunPrediction.wdir_tgl_10.name,
        }
        station_data = station_data.rename(rename_dict)

        return ModelRunProcessResult(
            model_run_info=grib_info, url=herbie_instance.grib, data=station_data
        )
