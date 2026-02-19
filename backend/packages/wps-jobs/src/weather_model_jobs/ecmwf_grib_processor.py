"""Processes downloaded ECMWF GRIB2 files into station-level weather data.

Uses cfgrib/xarray to read GRIB data, compute derived fields (wind speed,
direction, RH), extract nearest-neighbor station values, and convert units.
"""

import logging

import numpy as np
import pandas as pd
import xarray as xr

from wps_shared.db.models.weather_models import ModelRunPrediction
from weather_model_jobs.utils.process_grib import calculate_relative_humidity, convert_kelvin_to_celsius, convert_mps_to_kph

logger = logging.getLogger(__name__)

# ECMWF GRIB short names for the variables we work with
TEMP_FIELD = "t2m"
DEW_FIELD = "d2m"
U_WIND_FIELD = "u10"
V_WIND_FIELD = "v10"
PRECIP_FIELD = "tp"

# Derived fields
WIND_SPEED_FIELD = "si10"
WIND_DIR_FIELD = "wdir10"
RH_FIELD = "rh"


class ECMWFGribProcessor:
    """Processes a downloaded ECMWF GRIB2 file into station-level weather data."""

    def process(self, grib_path: str, stations_df: pd.DataFrame) -> xr.Dataset:
        """Process a GRIB file and extract station-level data.

        :param grib_path: path to the downloaded GRIB2 file
        :param stations_df: DataFrame with station info (must have latitude, longitude, code columns)
        :return: xarray Dataset with weather variables indexed by station code
        """
        ds = self._load_weather_dataset(grib_path)
        ds = self._compute_wind(ds)
        ds = self._extract_station_data(ds, stations_df)
        ds = self._convert_units(ds)
        ds = self._rename_to_db_fields(ds)
        return ds

    def _load_weather_dataset(self, grib_path: str) -> xr.Dataset:
        """Load all relevant variables from a GRIB file into a single dataset."""
        datasets = []
        # cfgrib splits GRIB messages by type; we may need multiple filter_by_keys
        # to load surface-level and instant fields separately.
        try:
            # Try loading all at once first
            ds = xr.open_dataset(grib_path, engine="cfgrib")
            datasets.append(ds)
        except Exception:
            # Fall back to loading with separate filters for different level types
            for type_of_level in ["heightAboveGround", "surface"]:
                try:
                    ds = xr.open_dataset(
                        grib_path,
                        engine="cfgrib",
                        backend_kwargs={"filter_by_keys": {"typeOfLevel": type_of_level}},
                    )
                    datasets.append(ds)
                except Exception:
                    continue

        if not datasets:
            raise ValueError(f"Could not load any data from {grib_path}")

        return xr.merge(datasets, compat="override")

    def _compute_wind(self, ds: xr.Dataset) -> xr.Dataset:
        """Compute wind speed and direction from u10/v10 components."""
        u = ds[U_WIND_FIELD]
        v = ds[V_WIND_FIELD]

        # Wind speed: sqrt(u^2 + v^2)
        ds[WIND_SPEED_FIELD] = np.sqrt(u**2 + v**2)

        # Wind direction: meteorological convention (direction wind comes FROM)
        wind_dir_math = np.degrees(np.arctan2(u, v))
        # Convert to "from" direction and ensure 0-360 range
        ds[WIND_DIR_FIELD] = (wind_dir_math + 180) % 360

        return ds

    def _extract_station_data(self, ds: xr.Dataset, stations_df: pd.DataFrame) -> xr.Dataset:
        """Extract nearest-neighbor values for each station location."""
        lats = xr.DataArray(stations_df["latitude"].values, dims="point")
        lons = xr.DataArray(stations_df["longitude"].values, dims="point")

        station_ds = ds.sel(latitude=lats, longitude=lons, method="nearest")

        # Add station codes as a coordinate
        station_ds = station_ds.assign_coords(point_code=("point", stations_df["code"].values))
        station_ds = station_ds.swap_dims({"point": "point_code"})

        return station_ds

    def _convert_units(self, ds: xr.Dataset) -> xr.Dataset:
        """Convert units to match database expectations."""
        # Temperature: Kelvin -> Celsius
        ds[TEMP_FIELD] = xr.apply_ufunc(convert_kelvin_to_celsius, ds[TEMP_FIELD])

        # Calculate RH from temp and dew point (both still in Kelvin at this point for dew point)
        ds[RH_FIELD] = xr.apply_ufunc(calculate_relative_humidity, ds[TEMP_FIELD] + 273.15, ds[DEW_FIELD])
        # Now convert dew point (not stored, but used for RH)
        # RH is already calculated, so we don't need to keep dew point

        # Wind speed: m/s -> km/h
        ds[WIND_SPEED_FIELD] = xr.apply_ufunc(convert_mps_to_kph, ds[WIND_SPEED_FIELD])

        # Precipitation: m -> mm
        ds[PRECIP_FIELD] = ds[PRECIP_FIELD] * 1000

        return ds

    def _rename_to_db_fields(self, ds: xr.Dataset) -> xr.Dataset:
        """Rename fields to match database column names."""
        rename_dict = {
            TEMP_FIELD: ModelRunPrediction.tmp_tgl_2.name,
            RH_FIELD: ModelRunPrediction.rh_tgl_2.name,
            PRECIP_FIELD: ModelRunPrediction.apcp_sfc_0.name,
            WIND_SPEED_FIELD: ModelRunPrediction.wind_tgl_10.name,
            WIND_DIR_FIELD: ModelRunPrediction.wdir_tgl_10.name,
        }
        return ds.rename(rename_dict)
