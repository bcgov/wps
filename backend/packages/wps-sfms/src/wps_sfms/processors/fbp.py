"""
FBP (Fire Behaviour Prediction) processor for calculating the raster Primary outputs
(ROS, CFB, SFC, CFC, TFC, HFI, RAZ, FD) from FBP System input rasters.

Mirrors the shape of processors/fwi.py (dataset-in, array-out calculation), but without
the S3/dependency-key orchestration layer that module has - there's no production job
consuming FBP rasters yet, this exists to validate the raster calculation chain against
the GLC-X-10 test dataset.
"""

from dataclasses import dataclass

import numpy as np
from wps_shared.fbp import vectorized_fbp_primary
from wps_shared.geospatial.wps_dataset import WPSDataset


@dataclass
class FBPPrimaryResult:
    ros: np.ndarray
    cfb: np.ndarray
    sfc: np.ndarray
    cfc: np.ndarray
    tfc: np.ndarray
    hfi: np.ndarray
    raz: np.ndarray
    fd: np.ndarray  # integer codes - see wps_shared.fbp.FIRE_DESCRIPTION_BY_CODE


@dataclass
class FBPInputDatasets:
    """One WPSDataset per FBP System input raster.

    `fuel_type` must be an integer-coded raster; `fuel_type_codes` maps each integer
    code to its FBP fuel type string (e.g. {1: "C1", 2: "C2", ...}). Unmapped/nodata
    codes are treated as fuel type "NF" (non-fuel), matching how the cffdrs package
    itself zeroes out results for that fuel type.

    All rasters must share the same grid (dimensions, geotransform, projection) - the
    caller is responsible for ensuring/warping this beforehand.
    """

    fuel_type: WPSDataset
    fuel_type_codes: dict[int, str]
    ffmc: WPSDataset
    bui: WPSDataset
    wind_speed: WPSDataset
    wind_direction: WPSDataset
    ground_slope: WPSDataset
    aspect: WPSDataset
    latitude: WPSDataset
    longitude: WPSDataset
    elevation: WPSDataset
    day_of_year: WPSDataset
    date_of_minimum_fmc: WPSDataset
    percent_conifer: WPSDataset
    percent_dead_fir: WPSDataset
    grass_curing: WPSDataset
    grass_fuel_load: WPSDataset


def calculate_fbp_primary(datasets: FBPInputDatasets) -> FBPPrimaryResult:
    """Calculates the FBP System Primary outputs for every pixel across the given input
    rasters.
    """
    fuel_type_codes, _ = datasets.fuel_type.replace_nodata_with(-1)
    to_fuel_type = np.vectorize(lambda code: datasets.fuel_type_codes.get(int(code), "NF"))
    fuel_type = to_fuel_type(fuel_type_codes)

    ffmc, _ = datasets.ffmc.replace_nodata_with(np.nan)
    bui, _ = datasets.bui.replace_nodata_with(np.nan)
    ws, _ = datasets.wind_speed.replace_nodata_with(np.nan)
    wd, _ = datasets.wind_direction.replace_nodata_with(np.nan)
    gs, _ = datasets.ground_slope.replace_nodata_with(np.nan)
    aspect, _ = datasets.aspect.replace_nodata_with(np.nan)
    lat, _ = datasets.latitude.replace_nodata_with(np.nan)
    lon, _ = datasets.longitude.replace_nodata_with(np.nan)
    elv, _ = datasets.elevation.replace_nodata_with(np.nan)
    dj, _ = datasets.day_of_year.replace_nodata_with(np.nan)
    d0, _ = datasets.date_of_minimum_fmc.replace_nodata_with(np.nan)
    pc, _ = datasets.percent_conifer.replace_nodata_with(np.nan)
    pdf, _ = datasets.percent_dead_fir.replace_nodata_with(np.nan)
    cc, _ = datasets.grass_curing.replace_nodata_with(np.nan)
    gfl, _ = datasets.grass_fuel_load.replace_nodata_with(np.nan)

    ros, cfb, sfc, cfc, tfc, hfi, raz, fd = vectorized_fbp_primary(
        fuel_type, ffmc, bui, ws, wd, gs, aspect, lat, lon, elv, dj, d0, pc, pdf, cc, gfl
    )

    return FBPPrimaryResult(ros=ros, cfb=cfb, sfc=sfc, cfc=cfc, tfc=tfc, hfi=hfi, raz=raz, fd=fd)
