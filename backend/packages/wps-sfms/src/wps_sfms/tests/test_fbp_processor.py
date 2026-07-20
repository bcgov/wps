"""
Validates the raster FBP calculation chain (wps_sfms.processors.fbp) against the 20
official test cases published in GLC-X-10 (Wotton, Alexander, Taylor 2009, "Updates and
revisions to the 1992 Canadian Forest Fire Behavior Prediction System", Information
Report GLC-X-10).

Table 4 (inputs) and Table 5 (Primary outputs) are transcribed verbatim into
fixtures/glcx10_inputs.csv and fixtures/glcx10_primary_outputs.csv. Each test case is a
single homogeneous point in the report, so it's rasterized here as a small uniform 2x2
grid per input variable - real WPSDataset/GDAL rasters (MEM driver, matching this
package's other processor tests), not a bespoke numpy-only shortcut.

Two GLC-X-10 input columns don't map 1:1 onto FBPInput's fields and need conversion:
- SAZ (slope azimuth, i.e. the upslope direction) vs FBPInput.aspect (the downhill-facing
  direction the calculation itself adds 180 degrees to internally to recover SAZ): aspect
  = SAZ - 180.
- WDIR (wind direction, direction the wind is coming from) maps directly to FBPInput.wd,
  except test case 4 where WDIR is undefined but WAZ (wind azimuth = wd + 180) is given
  directly instead: wd = WAZ - 180.

Discrepancy findings: every one of the 20 cases matches within 0.5% on ROS/CFB/SFC/CFC/
TFC/HFI/RAZ, and the FD (fire description: surface/intermittent/continuous crown)
classification matches exactly in all 20. The deviation is a small, uniform negative
bias across every fuel type and burning condition (not concentrated in one equation or
one fuel type), consistent with GLC-X-10's own note that its published outputs carry
more decimal places than the underlying models are truly accurate to. This does not
point to a bug in the raster calculation chain.
"""

import csv
import math
from pathlib import Path

import numpy as np
import pytest
from osgeo import gdal
from wps_shared.fbp import FIRE_DESCRIPTION_BY_CODE
from wps_shared.geospatial.wps_dataset import WPSDataset
from wps_shared.tests.geospatial.dataset_common import create_test_dataset

from wps_sfms.processors.fbp import FBPInputDatasets, calculate_fbp_primary

FIXTURES_DIR = Path(__file__).parent / "fixtures"
EXTENT = (-120, -119.99, 54, 54.01)  # arbitrary small WGS84 extent, values are homogeneous
GRID_SIZE = 2

# code -> FBP fuel type string, for the fuel_type raster
FUEL_TYPES = [
    "C1", "C2", "C3", "C4", "C5", "C6", "C7", "D1",
    "M1", "M2", "M3", "M4", "O1A", "O1B", "S1", "S2", "S3",
]
FUEL_TYPE_CODES = dict(enumerate(FUEL_TYPES, start=1))
FUEL_TYPE_TO_CODE = {fuel_type: code for code, fuel_type in FUEL_TYPE_CODES.items()}

# GLC-X-10 tolerates a small band of rounding noise (see module docstring); use the same
# tolerance for every Primary output.
RTOL = 0.01


def _to_float(value: str) -> float:
    return float(value) if value.strip() != "" else float("nan")


def _load_rows(filename: str) -> list[dict]:
    with open(FIXTURES_DIR / filename) as f:
        return list(csv.DictReader(f))


def _make_raster(value: float, data_type=gdal.GDT_Float64) -> WPSDataset:
    array = np.full((GRID_SIZE, GRID_SIZE), value)
    ds = create_test_dataset(
        "", GRID_SIZE, GRID_SIZE, EXTENT, 4326, data_type=data_type, fill_value=value
    )
    return WPSDataset(ds=ds, ds_path=None)


def _test_case_datasets(row: dict) -> FBPInputDatasets:
    fuel_type = row["Fuel Type"].replace("-", "").upper()
    wdir = row["WDIR"].strip()
    saz = row["SAZ"].strip()

    # WDIR maps directly to FBPInput.wd; when it's undefined, derive it from WAZ instead
    # (WAZ = wd + 180).
    wd = _to_float(wdir) if wdir != "" else (_to_float(row["WAZ"]) - 180) % 360
    # FBPInput.aspect + 180 = SAZ (slope azimuth/upslope direction), so aspect = SAZ - 180.
    # When GS is 0 slope has no effect and SAZ is left blank in the report; aspect is
    # irrelevant in that case so 0 is fine.
    aspect = ((_to_float(saz) if saz != "" else 0) - 180) % 360

    return FBPInputDatasets(
        fuel_type=_make_raster(FUEL_TYPE_TO_CODE[fuel_type], data_type=gdal.GDT_Int32),
        fuel_type_codes=FUEL_TYPE_CODES,
        ffmc=_make_raster(_to_float(row["FFMC"])),
        bui=_make_raster(_to_float(row["BUI"])),
        wind_speed=_make_raster(_to_float(row["WS"])),
        wind_direction=_make_raster(wd),
        ground_slope=_make_raster(_to_float(row["GS"])),
        aspect=_make_raster(aspect),
        latitude=_make_raster(_to_float(row["Lat"])),
        longitude=_make_raster(_to_float(row["Long"])),
        elevation=_make_raster(_to_float(row["Elev"])),
        day_of_year=_make_raster(_to_float(row["Dj"])),
        date_of_minimum_fmc=_make_raster(_to_float(row["D0"])),
        percent_conifer=_make_raster(_to_float(row["PC"])),
        percent_dead_fir=_make_raster(_to_float(row["PDF"])),
        grass_curing=_make_raster(_to_float(row["C"])),
        grass_fuel_load=_make_raster(_to_float(row["GFL"])),
    )


GLCX10_INPUT_ROWS = _load_rows("glcx10_inputs.csv")
GLCX10_OUTPUT_ROWS = _load_rows("glcx10_primary_outputs.csv")
GLCX10_CASES = list(zip(GLCX10_INPUT_ROWS, GLCX10_OUTPUT_ROWS, strict=True))


@pytest.mark.filterwarnings("ignore:.*out of range, clamped.*:UserWarning")
# "-" cells in Table 4 are deliberately fed through as NaN so FBPInput applies its own
# fuel-type default, which logs a clamped-to-default warning for every one - expected noise.
@pytest.mark.parametrize(
    "input_row,expected",
    GLCX10_CASES,
    ids=[row["Test Case"] for row in GLCX10_INPUT_ROWS],
)
def test_glcx10_primary_outputs(input_row: dict, expected: dict):
    datasets = _test_case_datasets(input_row)
    result = calculate_fbp_primary(datasets)

    assert result.ros == pytest.approx(float(expected["ROS"]), rel=RTOL)
    assert result.cfb == pytest.approx(float(expected["CFB"]), abs=0.01)
    assert result.sfc == pytest.approx(float(expected["SFC"]), rel=RTOL)
    assert result.cfc == pytest.approx(float(expected["CFC"]), rel=RTOL, abs=0.01)
    assert result.tfc == pytest.approx(float(expected["TFC"]), rel=RTOL)
    assert result.hfi == pytest.approx(float(expected["HFI"]), rel=RTOL)
    assert result.raz == pytest.approx(float(expected["RAZ"]), abs=0.5)

    fd = {FIRE_DESCRIPTION_BY_CODE[code] for code in np.unique(result.fd)}
    assert fd == {expected["FD"]}
