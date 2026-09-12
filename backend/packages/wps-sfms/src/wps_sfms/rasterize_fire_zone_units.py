"""Rasterize fire zone unit identifiers onto an existing raster grid.

Run from the repository root using the configured object-store fire zones::

    uv run --project backend python -m wps_sfms.rasterize_fire_zone_units \
        --reference-raster /path/to/reference.tif \
        --output-raster /path/to/fire_zone_units.tif

Use a local fire zone source instead of the configured object store::

    uv run --project backend python -m wps_sfms.rasterize_fire_zone_units \
        --reference-raster /path/to/reference.tif \
        --output-raster /path/to/fire_zone_units.tif \
        --source-geojson /path/to/fire_zone_units.geojson

Replace an existing output raster::

    uv run --project backend python -m wps_sfms.rasterize_fire_zone_units \
        --reference-raster /path/to/reference.tif \
        --output-raster /path/to/fire_zone_units.tif \
        --overwrite
"""

import argparse
import os
import tempfile
from collections.abc import Sequence
from pathlib import Path

from osgeo import gdal, ogr
from wps_shared.geospatial.geospatial import rasters_match
from wps_shared.sfms.raster_addresser import BaseRasterAddresser, S3Key
from wps_shared.utils.s3 import gdal_s3_context

gdal.UseExceptions()

DEFAULT_FIRE_ZONE_KEY = S3Key("zone-units/fire_zone_units.geojson")
OBJECT_ID_FIELD = "OBJECTID"
# use zero as background so positive zone identifiers remain directly usable in raster math
OUTPUT_NODATA = 0


def default_fire_zone_path() -> str:
    """Return the GDAL path for the configured production fire zone source."""
    return BaseRasterAddresser().gdal_path(DEFAULT_FIRE_ZONE_KEY)


def _open_reference(reference_raster: str) -> gdal.Dataset:
    try:
        dataset = gdal.OpenEx(reference_raster, gdal.OF_RASTER | gdal.OF_READONLY)
    except RuntimeError as error:
        raise ValueError(f"Unable to open reference raster: {reference_raster}") from error
    if dataset is None:
        raise ValueError(f"Unable to open reference raster: {reference_raster}")
    if dataset.GetGeoTransform(can_return_null=True) is None:
        raise ValueError(f"Reference raster has no geotransform: {reference_raster}")
    if dataset.GetSpatialRef() is None:
        raise ValueError(f"Reference raster has no coordinate reference system: {reference_raster}")
    return dataset


def _open_fire_zones(source_geojson: str) -> tuple[gdal.Dataset, ogr.Layer]:
    try:
        dataset = gdal.OpenEx(source_geojson, gdal.OF_VECTOR | gdal.OF_READONLY)
    except RuntimeError as error:
        raise ValueError(f"Unable to open fire zone source: {source_geojson}") from error
    if dataset is None:
        raise ValueError(f"Unable to open fire zone source: {source_geojson}")

    layer = dataset.GetLayer(0)
    if layer is None:
        raise ValueError(f"Fire zone source has no vector layer: {source_geojson}")
    if layer.GetSpatialRef() is None:
        raise ValueError(f"Fire zone source has no coordinate reference system: {source_geojson}")

    field_index = layer.GetLayerDefn().GetFieldIndex(OBJECT_ID_FIELD)
    if field_index < 0:
        raise ValueError(f"Fire zone source is missing the {OBJECT_ID_FIELD} field")
    field_type = layer.GetLayerDefn().GetFieldDefn(field_index).GetType()
    if field_type not in (ogr.OFTInteger, ogr.OFTInteger64):
        raise ValueError(f"Fire zone {OBJECT_ID_FIELD} field must contain integers")
    return dataset, layer


def _create_output(output_path: Path, reference: gdal.Dataset) -> gdal.Dataset:
    driver = gdal.GetDriverByName("GTiff")
    if driver is None:
        raise RuntimeError("GDAL GeoTIFF driver is unavailable")
    output = driver.Create(
        str(output_path),
        reference.RasterXSize,
        reference.RasterYSize,
        1,
        gdal.GDT_Int32,
        options=["TILED=YES", "COMPRESS=DEFLATE", "BIGTIFF=IF_SAFER"],
    )
    if output is None:
        raise RuntimeError(f"Unable to create output raster: {output_path}")

    # burn into a pre-sized dataset so origin, rotation, resolution, and projection stay exact
    output.SetGeoTransform(reference.GetGeoTransform())
    output.SetProjection(reference.GetProjection())
    output_band = output.GetRasterBand(1)
    output_band.SetNoDataValue(OUTPUT_NODATA)
    output_band.SetDescription("fire_zone_objectid")
    output_band.Fill(OUTPUT_NODATA)
    return output


def rasterize_fire_zone_units(
    reference_raster: str,
    output_raster: str | Path,
    *,
    source_geojson: str | None = None,
    overwrite: bool = False,
) -> Path:
    """Rasterize fire zone OBJECTIDs onto the exact grid of a reference raster."""
    output_path = Path(output_raster)
    if output_path.exists() and not overwrite:
        raise FileExistsError(f"Output raster already exists: {output_path}")
    if output_path.is_dir():
        raise ValueError(f"Output raster path is a directory: {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # keep the temporary file beside the output so the final replacement is atomic
    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{output_path.stem}-",
        suffix=".tif",
        dir=output_path.parent,
    )
    os.close(file_descriptor)
    temporary_path = Path(temporary_name)
    temporary_path.unlink()

    source_path = source_geojson or default_fire_zone_path()
    reference = None
    source = None
    output = None
    rasterized = None
    try:
        # configure remote reads for the default zone source and any /vsis3 reference path
        with gdal_s3_context():
            try:
                reference = _open_reference(reference_raster)
                source, layer = _open_fire_zones(source_path)
                output = _create_output(temporary_path, reference)
                rasterized = gdal.Rasterize(
                    output,
                    source,
                    options=gdal.RasterizeOptions(
                        attribute=OBJECT_ID_FIELD,
                        # use pixel centres so shared borders do not become order-dependent overlaps
                        allTouched=False,
                        layers=[layer.GetName()],
                    ),
                )
                if rasterized is None:
                    raise RuntimeError("GDAL failed to rasterize the fire zones")
                output.FlushCache()
                if not rasters_match(output, reference):
                    raise RuntimeError("Output raster does not match the reference grid")
            finally:
                rasterized = None
                output = None
                source = None
                reference = None

        os.replace(temporary_path, output_path)
        return output_path
    finally:
        rasterized = None
        output = None
        source = None
        reference = None
        temporary_path.unlink(missing_ok=True)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Rasterize fire zone OBJECTIDs onto a reference raster grid."
    )
    parser.add_argument(
        "--reference-raster",
        required=True,
        help="Local or GDAL-readable reference raster path",
    )
    parser.add_argument(
        "--output-raster",
        required=True,
        type=Path,
        help="Local output GeoTIFF path",
    )
    parser.add_argument(
        "--source-geojson",
        help=(
            "Local or GDAL-readable fire zone source; defaults to "
            "zone-units/fire_zone_units.geojson in the configured object store"
        ),
    )
    parser.add_argument("--overwrite", action="store_true", help="Replace an existing output")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = build_arg_parser().parse_args(argv)
    try:
        output_path = rasterize_fire_zone_units(
            arguments.reference_raster,
            arguments.output_raster,
            source_geojson=arguments.source_geojson,
            overwrite=arguments.overwrite,
        )
    except (OSError, RuntimeError, ValueError) as error:
        raise SystemExit(str(error)) from error
    print(f"Fire zone raster: {output_path}")
    return 0


if __name__ == "__main__":
    main()
