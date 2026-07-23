"""
Validates cffdrs_vec.fbp (and cffdrs_vec.fwi.vectorized_isi) against the 20 published FBP System
test cases from GLC-X-10 (Wotton et al. 2009), Table 4 (inputs) and Table 5 (primary outputs).
See https://github.com/bcgov/wps/issues/4893.

The input/output CSVs are vendored from cffdrs_py's own test fixtures
(cffdrs/tests/data/test_fbp.csv, fbp_01.csv, fbp_04.csv) - the same GLC-X-10 dataset, but not
included in the installed package, so it's copied here rather than depended on at runtime.

Rather than calling a single all-in-one function, this test composes the individual vectorized
functions cffdrs_vec.fbp exports (foliar_moisture_content, surface_fuel_consumption,
slope_adjustment, rate_of_spread_extended, total_fuel_consumption, fire_intensity) the same way
cffdrs's own cffdrs.fire_behaviour_prediction._fire_behaviour_prediction orchestrates them for
its Primary output, but over batched arrays covering all 20 cases at once rather than one case
at a time - this is what these functions are for.

Note: an earlier version of this test validated app.fire_behaviour.prediction's *scalar*
calculate_fire_behaviour_prediction_using_cffdrs instead, and needed to xfail 17 of the 20 cases
because that wrapper hardcodes ground slope to 0, doesn't accept a D0 override, and hardcodes
grass fuel load to 0.35. None of those gaps exist here: this test calls the underlying cffdrs
functions directly with every published input, and all 20 cases match Table 5 within floating
point/rounding noise.
"""

import csv
import math
from pathlib import Path

import numpy as np
import pytest
from cffdrs.constants import D1, FUEL_TYPE_CODES, O1A, O1B, S1, S2, S3
from cffdrs_vec import fbp
from cffdrs_vec.fwi import vectorized_isi

DATA_DIR = Path(__file__).parent / "data"

# Fuel types with no crown to burn - _fire_behaviour_prediction always zeroes FMC for these.
_NO_CROWN_FUEL_TYPE_CODES = (D1, S1, S2, S3, O1A, O1B)

FIRE_TYPE_BY_FD_CODE = {"S": "SUR", "I": "IC", "C": "CC"}

# Table 7 (FCFDG 1992) CBH/CFL defaults, used because the GLC-X-10 dataset leaves CBH/CFL blank
# for every case (relying on cffdrs's own per-fuel-type defaults). Matches
# wps_shared.fuel_types.FUEL_TYPE_DEFAULTS exactly.
_CBH_DEFAULT = {
    "C1": 2, "C2": 3, "C3": 8, "C4": 4, "C5": 18, "C6": 7, "C7": 10, "D1": 0,
    "M1": 6, "M2": 6, "M3": 6, "M4": 6, "S1": 0, "S2": 0, "S3": 0, "O1A": 0, "O1B": 0,
}
_CFL_DEFAULT = {
    "C1": 0.75, "C2": 0.8, "C3": 1.15, "C4": 1.2, "C5": 1.2, "C6": 1.8, "C7": 0.5, "D1": 0,
    "M1": 0.8, "M2": 0.8, "M3": 0.8, "M4": 0.8, "S1": 0, "S2": 0, "S3": 0, "O1A": 0, "O1B": 0,
}
_PC_DEFAULT = {
    "C1": 100, "C2": 100, "C3": 100, "C4": 100, "C5": 100, "C6": 100, "C7": 100, "D1": 0,
    "M1": 50, "M2": 50, "M3": 0, "M4": 0, "S1": 0, "S2": 0, "S3": 0, "O1A": 0, "O1B": 0,
}
_PDF_DEFAULT = {
    "C1": 0, "C2": 0, "C3": 0, "C4": 0, "C5": 0, "C6": 0, "C7": 0, "D1": 0,
    "M1": 0, "M2": 0, "M3": 30, "M4": 30, "S1": 0, "S2": 0, "S3": 0, "O1A": 0, "O1B": 0,
}


def _parse_float(value: str) -> float:
    value = value.strip()
    if value == "" or value.upper() == "NA":
        return math.nan
    return float(value)


def _normalize_fuel_type(value: str) -> str:
    return value.strip().upper().replace("-", "")


def _with_default(values: np.ndarray, fuel_types: list, defaults: dict) -> np.ndarray:
    fallback = np.array([defaults[ft] for ft in fuel_types], dtype=np.float64)
    return np.where(np.isnan(values), fallback, values)


def _load_rows(filename: str) -> list[dict]:
    with open(DATA_DIR / filename) as f:
        return list(csv.DictReader(f))


class GLCX10Cases:
    """All 20 GLC-X-10 cases loaded as batched arrays, plus the published Table 5 outputs."""

    def __init__(self):
        input_rows = _load_rows("glc_x_10_inputs.csv")
        output_by_id = {row["ID"]: row for row in _load_rows("glc_x_10_primary_outputs.csv")}

        self.ids = [row["id"] for row in input_rows]
        self.fuel_types = [_normalize_fuel_type(row["FuelType"]) for row in input_rows]
        self.fuel_type_codes = np.array(
            [FUEL_TYPE_CODES[ft] for ft in self.fuel_types], dtype=np.int64
        )

        self.lat = np.array([_parse_float(row["LAT"]) for row in input_rows])
        self.lon = np.array([_parse_float(row["LONG"]) for row in input_rows])
        self.elv = np.nan_to_num(np.array([_parse_float(row["ELV"]) for row in input_rows]))
        self.ffmc = np.array([_parse_float(row["FFMC"]) for row in input_rows])
        self.bui = np.array([_parse_float(row["BUI"]) for row in input_rows])
        self.ws = np.array([_parse_float(row["WS"]) for row in input_rows])
        self.wd_rad = np.radians(
            np.nan_to_num(np.array([_parse_float(row["WD"]) for row in input_rows]))
        )
        self.gs = np.array([_parse_float(row["GS"]) for row in input_rows])
        self.dj = np.array([_parse_float(row["Dj"]) for row in input_rows])
        self.d0 = np.nan_to_num(np.array([_parse_float(row["D0"]) for row in input_rows]))
        self.aspect_rad = np.radians(
            np.nan_to_num(np.array([_parse_float(row["Aspect"]) for row in input_rows]))
        )
        self.gfl = np.nan_to_num(np.array([_parse_float(row["GFL"]) for row in input_rows]))

        self.pc = _with_default(
            np.array([_parse_float(row["PC"]) for row in input_rows]), self.fuel_types, _PC_DEFAULT
        )
        self.pdf = _with_default(
            np.array([_parse_float(row["PDF"]) for row in input_rows]),
            self.fuel_types,
            _PDF_DEFAULT,
        )
        self.cc = np.nan_to_num(np.array([_parse_float(row["cc"]) for row in input_rows]))
        self.cbh = _with_default(
            np.array([_parse_float(row["CBH"]) for row in input_rows]),
            self.fuel_types,
            _CBH_DEFAULT,
        )
        self.cfl = _with_default(
            np.array([_parse_float(row["CFL"]) for row in input_rows]),
            self.fuel_types,
            _CFL_DEFAULT,
        )

        self.expected_ros = np.array([float(output_by_id[i]["ROS"]) for i in self.ids])
        self.expected_hfi = np.array([float(output_by_id[i]["HFI"]) for i in self.ids])
        self.expected_cfb = np.array([float(output_by_id[i]["CFB"]) for i in self.ids])
        self.expected_sfc = np.array([float(output_by_id[i]["SFC"]) for i in self.ids])
        self.expected_tfc = np.array([float(output_by_id[i]["TFC"]) for i in self.ids])
        self.expected_raz = np.array([float(output_by_id[i]["RAZ"]) for i in self.ids])
        self.expected_fire_type = [FIRE_TYPE_BY_FD_CODE[output_by_id[i]["FD"]] for i in self.ids]


def calculate_primary_output(cases: GLCX10Cases):
    """Mirrors cffdrs.fire_behaviour_prediction._fire_behaviour_prediction's Primary output,
    composed from cffdrs_vec.fbp's vectorized functions over the whole batch at once.
    """
    n = len(cases.ids)

    # Corrections to reorient Wind Azimuth (WAZ) and Uphill slope azimuth (SAZ) - Eq. matches
    # _fire_behaviour_prediction exactly.
    waz = cases.wd_rad + math.pi
    waz = np.where(waz > 2 * math.pi, waz - 2 * math.pi, waz)
    saz = cases.aspect_rad + math.pi
    saz = np.where(saz > 2 * math.pi, saz - 2 * math.pi, saz)

    fmc = fbp.vectorized_foliar_moisture_content(cases.lat, cases.lon, cases.elv, cases.dj, cases.d0)
    no_crown = np.isin(cases.fuel_type_codes, _NO_CROWN_FUEL_TYPE_CODES)
    fmc = np.where(no_crown, 0.0, fmc)

    sfc = fbp.vectorized_surface_fuel_consumption(
        cases.fuel_type_codes, cases.ffmc, cases.bui, cases.pc, cases.gfl
    )

    # slope_adjustment()'s isi parameter is unused by the underlying formula (it derives its own
    # zero-wind ISI internally), so any placeholder value works here.
    wsv0, raz0 = fbp.vectorized_slope_adjustment(
        cases.fuel_type_codes,
        cases.ffmc,
        cases.bui,
        cases.ws,
        waz,
        cases.gs,
        saz,
        fmc,
        sfc,
        cases.pc,
        cases.pdf,
        cases.cc,
        cases.cbh,
        np.zeros(n),
    )
    slope_active = (cases.gs > 0) & (cases.ffmc > 0)
    wsv = np.where(slope_active, wsv0, cases.ws)
    raz = np.where(slope_active, raz0, waz)

    # All 20 published cases leave ISI as "not observed" (0), so it's always derived from the
    # slope-adjusted wind speed here, same as _fire_behaviour_prediction does.
    isi = vectorized_isi(cases.ffmc, wsv, True)

    ros, cfb, _csi, _rso = fbp.vectorized_rate_of_spread_extended(
        cases.fuel_type_codes, isi, cases.bui, fmc, sfc, cases.pc, cases.pdf, cases.cc, cases.cbh
    )
    cfb = np.where(cases.cfl > 0, cfb, 0.0)

    tfc = fbp.vectorized_total_fuel_consumption(
        cases.fuel_type_codes, cases.cfl, cfb, sfc, cases.pc, cases.pdf
    )
    hfi = fbp.vectorized_fire_intensity(tfc, ros)

    raz_deg = np.degrees(raz)
    raz_deg = np.where(raz_deg == 360, 0.0, raz_deg)

    fire_type = np.full(n, "IC", dtype=object)
    fire_type[cfb < 0.1] = "SUR"
    fire_type[cfb >= 0.9] = "CC"

    return ros, hfi, cfb, sfc, tfc, raz_deg, fire_type


@pytest.fixture(scope="module")
def cases():
    return GLCX10Cases()


def test_fbp_glc_x_10_ros(cases):
    ros, _, _, _, _, _, _ = calculate_primary_output(cases)
    np.testing.assert_allclose(ros, cases.expected_ros, rtol=1e-3, err_msg="ROS")


def test_fbp_glc_x_10_hfi(cases):
    _, hfi, _, _, _, _, _ = calculate_primary_output(cases)
    np.testing.assert_allclose(hfi, cases.expected_hfi, rtol=1e-3, err_msg="HFI")


def test_fbp_glc_x_10_cfb(cases):
    _, _, cfb, _, _, _, _ = calculate_primary_output(cases)
    np.testing.assert_allclose(cfb, cases.expected_cfb, atol=1e-3, err_msg="CFB")


def test_fbp_glc_x_10_sfc(cases):
    _, _, _, sfc, _, _, _ = calculate_primary_output(cases)
    np.testing.assert_allclose(sfc, cases.expected_sfc, rtol=1e-3, err_msg="SFC")


def test_fbp_glc_x_10_tfc(cases):
    _, _, _, _, tfc, _, _ = calculate_primary_output(cases)
    np.testing.assert_allclose(tfc, cases.expected_tfc, rtol=1e-3, err_msg="TFC")


def test_fbp_glc_x_10_raz(cases):
    _, _, _, _, _, raz, _ = calculate_primary_output(cases)
    np.testing.assert_allclose(raz, cases.expected_raz, atol=0.1, err_msg="RAZ")


def test_fbp_glc_x_10_fire_type(cases):
    _, _, _, _, _, _, fire_type = calculate_primary_output(cases)
    assert list(fire_type) == cases.expected_fire_type
