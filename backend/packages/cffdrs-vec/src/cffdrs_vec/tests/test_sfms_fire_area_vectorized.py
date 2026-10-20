"""
Validates `vectorized_elliptical_fire_area` against all 20 GLC-X-10 FBP System test cases
(Wotton et al. 2009), using each case's published time of interest.

The tests use the same two independent data sources as `test_fbp_glc_x_10.py`:
- `paper`: expected area comes from Table 6's A column.
- `r_package`: expected area is calculated from the published DH, DB, and LBt values using
  equation 86 on page 49 of ST-X-3: A = pi * (D_T)^2 / (40000 * LBt), where D_T = DH + DB.

`source.load()` supplies the FBP inputs and primary expected outputs. Area calculation also needs
the time of interest, FMC, ISI, and expected area, which `source.load_area_cases()` assembles from
the relevant input and output tables.

The published areas are rounded, so comparisons allow a 0.5% relative difference and an absolute
difference of 0.01 ha for values near zero.

`test_fire_area_glc_x_10` reads inputs from the CSV files. `test_fire_area_glc_x_10_rasters` runs
the same cases using the GeoTIFF input fixtures, checking the calculation with 2-D raster-shaped
arrays. Time, FMC, ISI, and expected area are loaded from the CSV files and reshaped to match the
raster inputs because no fixtures for those values are provided.
"""

import numpy as np
import pytest

from cffdrs_vec.fbp import vectorized_elliptical_fire_area
from cffdrs_vec.tests._glc_x_10_data import GLC_X_10_SOURCES

RTOL_AREA = 0.005
ATOL_AREA = 0.01


@pytest.mark.parametrize("source", GLC_X_10_SOURCES, ids=lambda s: s.name)
def test_fire_area_glc_x_10(source):
    inputs, _ = source.load()
    area_cases = source.load_area_cases()

    result = vectorized_elliptical_fire_area(
        inputs.fuel_type_codes,
        inputs.ffmc,
        inputs.bui,
        inputs.ws,
        inputs.wd_rad,
        inputs.gs,
        inputs.aspect_rad,
        inputs.pc,
        inputs.pdf,
        inputs.cc,
        inputs.gfl,
        inputs.cbh,
        inputs.cfl,
        area_cases.fmc,
        area_cases.isi,
        area_cases.time_min,
    )

    np.testing.assert_allclose(
        result, area_cases.expected_area_ha, rtol=RTOL_AREA, atol=ATOL_AREA, err_msg="Area"
    )


@pytest.mark.parametrize("source", GLC_X_10_SOURCES, ids=lambda s: s.name)
def test_fire_area_glc_x_10_rasters(source):
    inputs = source.load_raster_inputs()
    area_cases = source.load_area_cases()
    # Raster inputs are 2D, while these case values loaded from CSV are 1D; reshape them to match.
    shape = inputs.fuel_type_codes.shape

    result = vectorized_elliptical_fire_area(
        inputs.fuel_type_codes,
        inputs.ffmc,
        inputs.bui,
        inputs.ws,
        inputs.wd_rad,
        inputs.gs,
        inputs.aspect_rad,
        inputs.pc,
        inputs.pdf,
        inputs.cc,
        inputs.gfl,
        inputs.cbh,
        inputs.cfl,
        area_cases.fmc.reshape(shape),
        area_cases.isi.reshape(shape),
        area_cases.time_min.reshape(shape),
    )

    # Check shape explicitly because assert_allclose can broadcast differently shaped arrays.
    assert result.shape == shape
    np.testing.assert_allclose(
        result,
        area_cases.expected_area_ha.reshape(shape),
        rtol=RTOL_AREA,
        atol=ATOL_AREA,
        err_msg="Area",
    )
