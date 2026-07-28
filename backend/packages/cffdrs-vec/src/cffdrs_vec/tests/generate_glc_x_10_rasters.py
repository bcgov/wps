"""
Generates the GeoTIFF fixtures under fixtures/glc_x_10/ and fixtures/glc_x_10_paper/, via each
GLCX10Source's own generate_rasters() (see _glc_x_10_data.py for exactly what gets written and
why).

Not a test_*.py module - this is a one-off generator, run directly:
    uv run --package wps-api python -m cffdrs_vec.tests.generate_glc_x_10_rasters
The output is committed to the repo like the other raster fixtures, so this only needs re-running
if the source CSVs change.
"""

from cffdrs_vec.tests._glc_x_10_data import GLC_X_10_SOURCES


def main() -> None:
    for source in GLC_X_10_SOURCES:
        source.generate_rasters()


if __name__ == "__main__":
    main()
