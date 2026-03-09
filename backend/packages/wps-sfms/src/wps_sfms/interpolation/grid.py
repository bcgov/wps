from dataclasses import dataclass
from typing import Optional

import numpy as np
from numpy.typing import NDArray
from wps_shared.geospatial.geospatial import rasters_match
from wps_shared.geospatial.wps_dataset import WPSDataset


@dataclass(frozen=True)
class GridContext:
    """Shared raster grid state for interpolation workflows."""

    geotransform: tuple[float, ...]
    projection: str
    x_size: int
    y_size: int
    valid_mask: NDArray[np.bool_]
    valid_lats: NDArray[np.float32]
    valid_lons: NDArray[np.float32]
    valid_yi: NDArray[np.intp]
    valid_xi: NDArray[np.intp]
    total_pixels: int
    skipped_nodata_count: int
    valid_dem_values: Optional[NDArray[np.float32]] = None
    temperature_data: Optional[NDArray[np.float32]] = None


def build_grid_context(
    reference_raster_path: str,
    mask_path: str,
    *,
    dem_path: Optional[str] = None,
    temperature_raster_path: Optional[str] = None,
) -> GridContext:
    """Load the shared raster state used by interpolation routines."""
    with WPSDataset(reference_raster_path) as ref_ds:
        geotransform = ref_ds.ds.GetGeoTransform()
        if geotransform is None:
            raise ValueError(
                f"Failed to get geotransform from reference raster: {reference_raster_path}"
            )
        projection = ref_ds.ds.GetProjection()
        x_size = ref_ds.ds.RasterXSize
        y_size = ref_ds.ds.RasterYSize

        with WPSDataset(mask_path) as mask_ds:
            valid_mask = ref_ds.apply_mask(mask_ds.warp_to_match(ref_ds))

        valid_lats, valid_lons, valid_yi, valid_xi = ref_ds.get_lat_lon_coords(valid_mask)
        total_pixels = x_size * y_size
        skipped_nodata_count = total_pixels - len(valid_yi)

        valid_dem_values = None
        if dem_path is not None:
            with WPSDataset(dem_path) as dem_ds:
                _validate_matching_grid(ref_ds, dem_ds, "DEM")
                dem_band = dem_ds.ds.GetRasterBand(1)
                dem_data = dem_band.ReadAsArray()
                if dem_data is None:
                    raise ValueError("Failed to read DEM data")
                valid_dem_values = dem_data[valid_mask].astype(np.float32, copy=False)

        temperature_data = None
        if temperature_raster_path is not None:
            with WPSDataset(temperature_raster_path) as temp_ds:
                _validate_matching_grid(ref_ds, temp_ds, "temperature raster")
                temp_band = temp_ds.ds.GetRasterBand(1)
                temp_data = temp_band.ReadAsArray()
                if temp_data is None:
                    raise ValueError("Failed to read temperature raster data")
                temperature_data = temp_data.astype(np.float32, copy=False)

    return GridContext(
        geotransform=tuple(geotransform),
        projection=projection,
        x_size=x_size,
        y_size=y_size,
        valid_mask=valid_mask.astype(np.bool_, copy=False),
        valid_lats=valid_lats.astype(np.float32, copy=False),
        valid_lons=valid_lons.astype(np.float32, copy=False),
        valid_yi=valid_yi.astype(np.intp, copy=False),
        valid_xi=valid_xi.astype(np.intp, copy=False),
        total_pixels=total_pixels,
        skipped_nodata_count=skipped_nodata_count,
        valid_dem_values=valid_dem_values,
        temperature_data=temperature_data,
    )


def _validate_matching_grid(reference_ds: WPSDataset, candidate_ds: WPSDataset, label: str) -> None:
    if not rasters_match(reference_ds.ds, candidate_ds.ds):
        raise ValueError(f"{label} grid does not match reference raster")
