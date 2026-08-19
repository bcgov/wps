"""Validation for loaded Fire Behaviour Prediction input rasters."""

import numpy as np

from wps_sfms.fbp_fuel_types import PERCENT_CONIFER_GRID_VALUES


def validate_percent_conifer(fuel: np.ndarray, percent_conifer: np.ndarray) -> None:
    """Require percent conifer to be present and within range on M1/M2 pixels."""
    mixedwood_mask = np.isin(fuel, tuple(PERCENT_CONIFER_GRID_VALUES))
    invalid = mixedwood_mask & (
        ~np.isfinite(percent_conifer) | (percent_conifer < 0) | (percent_conifer > 100)
    )
    if np.any(invalid):
        raise ValueError(
            "Percent-conifer raster contains missing or out-of-range values on mixedwood pixels"
        )
