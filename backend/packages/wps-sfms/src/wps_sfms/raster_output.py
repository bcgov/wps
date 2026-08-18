"""Shared construction of final masked SFMS calculation rasters."""

from contextlib import contextmanager
from typing import Generator

import numpy as np
from wps_shared.geospatial.wps_dataset import WPSDataset

from wps_sfms.sfmsng_raster_addresser import SFMSNGRasterAddresser


@contextmanager
def open_bc_mask_dataset() -> Generator[WPSDataset, None, None]:
    """Open the configured BC mask used to constrain calculated SFMS outputs."""
    mask_path = SFMSNGRasterAddresser().get_mask_key()
    with WPSDataset(mask_path) as mask:
        yield mask


@contextmanager
def create_masked_output_dataset(
    values: np.ndarray,
    reference: WPSDataset,
    nodata_value: float,
) -> Generator[WPSDataset, None, None]:
    """Create an output dataset with the BC mask enforced as the final value boundary."""
    with open_bc_mask_dataset() as mask:
        valid_mask = reference.apply_mask(mask)
        if values.shape != valid_mask.shape:
            raise ValueError(
                "Output array shape does not match reference grid: "
                f"{values.shape} vs {valid_mask.shape}"
            )

        # cast before masking so GDAL does not convert Float64 nodata to Float32 inconsistently
        masked_values = values.astype(np.float32, copy=True)
        masked_values[~valid_mask] = nodata_value
    reference_ds = reference.as_gdal_ds()

    with WPSDataset.from_array(
        masked_values,
        reference_ds.GetGeoTransform(),
        reference_ds.GetProjection(),
        nodata_value,
    ) as output_ds:
        yield output_ds
