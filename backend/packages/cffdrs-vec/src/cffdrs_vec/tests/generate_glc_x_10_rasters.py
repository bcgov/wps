"""
Generates the GeoTIFF fixtures under fixtures/glc_x_10/ and fixtures/glc_x_10_paper/, from each
GLCX10Source's own input/output CSVs (see _glc_x_10_data.py for the source definitions, and
GLCX10Source.load_raster_inputs() for how the raster fixtures generated here get read back).

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
    GLC_X_10_SOURCES,
    INPUT_RASTER_NAMES,
    OUTPUT_RASTER_NAMES,
    GLCX10Source,
    load_rows,
    normalize_fuel_type,
    parse_float,
)

SFMS_NO_DATA = -3.4028235e38
# 1 row x 20 columns, one pixel per case, in an arbitrary-but-valid location/resolution - the
# geospatial placement is meaningless here (LAT/LONG are separate data layers, not implied by
# pixel position), it just needs to be internally consistent across all rasters.
RASTER_GEOTRANSFORM = (-140.0, 1.0, 0.0, 60.0, 0.0, -1.0)


def _raster_projection_wkt() -> str:
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)
    return srs.ExportToWkt()


def _write_raster(raster_dir: Path, name: str, values: list) -> None:
    array = np.array([values], dtype=np.float32)  # shape (1, 20)
    array = np.where(np.isnan(array), SFMS_NO_DATA, array)
    with WPSDataset.from_array(
        array, RASTER_GEOTRANSFORM, _raster_projection_wkt(), SFMS_NO_DATA
    ) as ds:
        ds.export_to_geotiff(str(raster_dir / f"{name}.tif"))


def generate_rasters(source: GLCX10Source) -> None:
    """Writes `source`'s GeoTIFF fixtures under source.raster_dir - one small (1 row x 20 case)
    raster per input/output variable, in case order (column 0 = case 1, ..., column 19 = case
    20). Same one-raster-per-variable layout as the existing bui20240528.tif/dc20240528.tif/
    dmc20240528.tif FWI fixtures.

    Blank CSV cells (eg. CBH/CFL/PC, left for cffdrs to default) are written as SFMS_NO_DATA, not
    0 or NaN, so reading them back through WPSDataset.replace_nodata_with(np.nan) round-trips to
    exactly the same "missing" signal parse_float() gives when reading the CSV directly - see
    GLCX10Source.load_raster_inputs().
    """
    input_rows = load_rows(source.input_csv)
    output_by_id = {row[source.id_output_col]: row for row in load_rows(source.output_csv)}
    ids = [row[source.id_input_col] for row in input_rows]
    fuel_types = [normalize_fuel_type(row["FuelType"]) for row in input_rows]
    columns = source.columns

    aspect_deg, cbh, cfl = source.raster_aspect_cbh_cfl(input_rows)

    input_columns = {
        "fuel_type_code": [float(FUEL_TYPE_CODES[ft]) for ft in fuel_types],
        "lat": [parse_float(row[columns["lat"]]) for row in input_rows],
        "lon": [parse_float(row[columns["lon"]]) for row in input_rows],
        "elv": [parse_float(row[columns["elv"]]) for row in input_rows],
        "ffmc": [parse_float(row[columns["ffmc"]]) for row in input_rows],
        "bui": [parse_float(row[columns["bui"]]) for row in input_rows],
        "ws": [parse_float(row[columns["ws"]]) for row in input_rows],
        "wd": [parse_float(row[columns["wd"]]) for row in input_rows],
        "gs": [parse_float(row[columns["gs"]]) for row in input_rows],
        "dj": [parse_float(row[columns["dj"]]) for row in input_rows],
        "d0": [parse_float(row[columns["d0"]]) for row in input_rows],
        "aspect": aspect_deg,
        "pc": [parse_float(row[columns["pc"]]) for row in input_rows],
        "pdf": [parse_float(row[columns["pdf"]]) for row in input_rows],
        "cc": [parse_float(row[columns["cc"]]) for row in input_rows],
        "gfl": [parse_float(row[columns["gfl"]]) for row in input_rows],
        "cbh": cbh,
        "cfl": cfl,
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

    source.raster_dir.mkdir(parents=True, exist_ok=True)
    for name, values in {**input_columns, **output_columns}.items():
        _write_raster(source.raster_dir, name, values)
        print(f"wrote {source.raster_dir / f'{name}.tif'}")


def main() -> None:
    for source in GLC_X_10_SOURCES:
        generate_rasters(source)


if __name__ == "__main__":
    main()
