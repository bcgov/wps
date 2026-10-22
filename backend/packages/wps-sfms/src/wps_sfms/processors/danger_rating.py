"""Interpolate station danger ratings as whole classes."""

import numpy as np
from wps_shared.geospatial.wps_dataset import WPSDataset

from wps_sfms.processors.idw import Interpolator


class DangerRatingInterpolator(Interpolator):
    """Apply station IDW, then write valid pixels as classes from 1 to 5."""

    def interpolate(self, reference_raster_path: str) -> WPSDataset:
        dataset = super().interpolate(reference_raster_path)
        nodata = dataset.require_nodata_value()
        band = dataset.ds.GetRasterBand(dataset.band)
        for window in dataset.iter_windows():
            values = window.array
            valid = values != nodata
            # round halfway values up so 2.5 becomes class 3
            values[valid] = np.clip(np.floor(values[valid] + 0.5), 1, 5)
            band.WriteArray(values, window.x_offset, window.y_offset)
        band.FlushCache()
        return dataset
