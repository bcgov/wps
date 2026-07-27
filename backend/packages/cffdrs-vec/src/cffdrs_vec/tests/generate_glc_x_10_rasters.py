"""
Generates the GeoTIFF fixtures under fixtures/glc_x_10/ and fixtures/glc_x_10_paper/ - one small
raster per input/output variable, each holding all 20 published GLC-X-10 test cases as pixels in
a single 1x20 row, in case order (column 0 = case 1, ..., column 19 = case 20). Same
one-raster-per-variable layout as the existing bui20240528.tif/dc20240528.tif/dmc20240528.tif FWI
fixtures.

fixtures/glc_x_10/ is sourced from the vendored R cffdrs test CSVs (data/cffdrs_r_test_fbp_inputs.csv,
data/cffdrs_r_test_fbp_primary_outputs.csv). fixtures/glc_x_10_paper/ is sourced from the CSVs
transcribed directly from the published PDF (data/glc_x_10_paper_inputs.csv,
data/glc_x_10_paper_primary_outputs.csv) - see _glc_x_10_data.py for exact provenance of both.

Blank CSV cells (eg. CBH/CFL/PC, left for cffdrs to default) are written as SFMS_NO_DATA, not 0 or
NaN, so reading them back through WPSDataset.replace_nodata_with(np.nan) round-trips to exactly
the same "missing" signal _glc_x_10_data.parse_float() gives when reading the CSV directly - see
test_fbp_glc_x_10_rasters.py / test_fbp_glc_x_10_paper_rasters.py.

Not a test_*.py module - this is a one-off generator, run directly:
    uv run --package wps-api python -m cffdrs_vec.tests.generate_glc_x_10_rasters
The output is committed to the repo like the other raster fixtures, so this only needs re-running
if the source CSVs change.
"""

from pathlib import Path

import numpy as np
from cffdrs.constants import FUEL_TYPE_CODES
from osgeo import osr
from wps_shared.geospatial.wps_dataset import WPSDataset

from cffdrs_vec.tests._glc_x_10_data import (
    INPUT_RASTER_NAMES,
    OUTPUT_RASTER_NAMES,
    PAPER_RASTER_DIR,
    RASTER_DIR,
    load_rows,
    normalize_fuel_type,
    parse_float,
)

SFMS_NO_DATA = -3.4028235e38

# 1 row x 20 columns, one pixel per case, in an arbitrary-but-valid location/resolution - the
# geospatial placement is meaningless here (LAT/LONG are separate data layers, not implied by
# pixel position), it just needs to be internally consistent across all rasters.
GEOTRANSFORM = (-140.0, 1.0, 0.0, 60.0, 0.0, -1.0)


def _projection_wkt() -> str:
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)
    return srs.ExportToWkt()


def _write_raster(raster_dir: Path, name: str, values: list) -> None:
    array = np.array([values], dtype=np.float32)  # shape (1, 20)
    array = np.where(np.isnan(array), SFMS_NO_DATA, array)
    with WPSDataset.from_array(array, GEOTRANSFORM, _projection_wkt(), SFMS_NO_DATA) as ds:
        ds.export_to_geotiff(str(raster_dir / f"{name}.tif"))


def _r_package_columns() -> tuple[dict, dict]:
    input_rows = load_rows("cffdrs_r_test_fbp_inputs.csv")
    output_by_id = {row["ID"]: row for row in load_rows("cffdrs_r_test_fbp_primary_outputs.csv")}
    ids = [row["id"] for row in input_rows]
    fuel_types = [normalize_fuel_type(row["FuelType"]) for row in input_rows]

    input_columns = {
        "fuel_type_code": [float(FUEL_TYPE_CODES[ft]) for ft in fuel_types],
        "lat": [parse_float(row["LAT"]) for row in input_rows],
        "lon": [parse_float(row["LONG"]) for row in input_rows],
        "elv": [parse_float(row["ELV"]) for row in input_rows],
        "ffmc": [parse_float(row["FFMC"]) for row in input_rows],
        "bui": [parse_float(row["BUI"]) for row in input_rows],
        "ws": [parse_float(row["WS"]) for row in input_rows],
        "wd": [parse_float(row["WD"]) for row in input_rows],
        "gs": [parse_float(row["GS"]) for row in input_rows],
        "dj": [parse_float(row["Dj"]) for row in input_rows],
        "d0": [parse_float(row["D0"]) for row in input_rows],
        "aspect": [parse_float(row["Aspect"]) for row in input_rows],
        "pc": [parse_float(row["PC"]) for row in input_rows],
        "pdf": [parse_float(row["PDF"]) for row in input_rows],
        "cc": [parse_float(row["cc"]) for row in input_rows],
        "gfl": [parse_float(row["GFL"]) for row in input_rows],
        "cbh": [parse_float(row["CBH"]) for row in input_rows],
        "cfl": [parse_float(row["CFL"]) for row in input_rows],
    }
    assert list(input_columns) == INPUT_RASTER_NAMES

    output_columns = {
        "ros": [float(output_by_id[i]["ROS"]) for i in ids],
        "hfi": [float(output_by_id[i]["HFI"]) for i in ids],
        "cfb": [float(output_by_id[i]["CFB"]) for i in ids],
        "sfc": [float(output_by_id[i]["SFC"]) for i in ids],
        "tfc": [float(output_by_id[i]["TFC"]) for i in ids],
        "raz": [float(output_by_id[i]["RAZ"]) for i in ids],
    }
    assert list(output_columns) == OUTPUT_RASTER_NAMES

    return input_columns, output_columns


def _paper_columns() -> tuple[dict, dict]:
    input_rows = load_rows("glc_x_10_paper_inputs.csv")
    output_by_case = {
        row["TestCase"]: row for row in load_rows("glc_x_10_paper_primary_outputs.csv")
    }
    ids = [row["TestCase"] for row in input_rows]
    fuel_types = [normalize_fuel_type(row["FuelType"]) for row in input_rows]

    # The paper gives SAZ (upslope azimuth) directly rather than cffdrs's own Aspect
    # (downslope-facing direction) input convention; SAZ = Aspect + 180 deg (see fbp.r comments),
    # so invert that here - same order of operations as PaperGLCX10Cases (nan_to_num blank SAZ,
    # case 14 only, to 0 *before* the mod-360 conversion), so the CSV-direct and raster-sourced
    # paths resolve to the exact same aspect value even though it doesn't affect any result
    # (case 14 has GS=0, so slope direction is never actually used).
    saz = np.nan_to_num(np.array([parse_float(row["SAZ"]) for row in input_rows]))
    aspect = (saz - 180) % 360

    input_columns = {
        "fuel_type_code": [float(FUEL_TYPE_CODES[ft]) for ft in fuel_types],
        "lat": [parse_float(row["Lat"]) for row in input_rows],
        "lon": [parse_float(row["Long"]) for row in input_rows],
        "elv": [parse_float(row["Elev"]) for row in input_rows],
        "ffmc": [parse_float(row["FFMC"]) for row in input_rows],
        "bui": [parse_float(row["BUI"]) for row in input_rows],
        "ws": [parse_float(row["WS"]) for row in input_rows],
        "wd": [parse_float(row["WDIR"]) for row in input_rows],
        "gs": [parse_float(row["GS"]) for row in input_rows],
        "dj": [parse_float(row["Dj"]) for row in input_rows],
        "d0": [parse_float(row["D0"]) for row in input_rows],
        "aspect": list(aspect),
        "pc": [parse_float(row["PC"]) for row in input_rows],
        "pdf": [parse_float(row["PDF"]) for row in input_rows],
        "cc": [parse_float(row["C"]) for row in input_rows],
        "gfl": [parse_float(row["GFL"]) for row in input_rows],
        # Table 4 has no CBH/CFL columns at all - always missing, always defaulted on read.
        "cbh": [float("nan")] * len(input_rows),
        "cfl": [float("nan")] * len(input_rows),
    }
    assert list(input_columns) == INPUT_RASTER_NAMES

    output_columns = {
        "ros": [float(output_by_case[i]["ROS"]) for i in ids],
        "hfi": [float(output_by_case[i]["HFI"]) for i in ids],
        "cfb": [float(output_by_case[i]["CFB"]) for i in ids],
        "sfc": [float(output_by_case[i]["SFC"]) for i in ids],
        "tfc": [float(output_by_case[i]["TFC"]) for i in ids],
        "raz": [float(output_by_case[i]["RAZ"]) for i in ids],
    }
    assert list(output_columns) == OUTPUT_RASTER_NAMES

    return input_columns, output_columns


def _generate(raster_dir: Path, input_columns: dict, output_columns: dict) -> None:
    raster_dir.mkdir(parents=True, exist_ok=True)
    for name, values in {**input_columns, **output_columns}.items():
        _write_raster(raster_dir, name, values)
        print(f"wrote {raster_dir / f'{name}.tif'}")


def main() -> None:
    _generate(RASTER_DIR, *_r_package_columns())
    _generate(PAPER_RASTER_DIR, *_paper_columns())


if __name__ == "__main__":
    main()
