from pathlib import Path

import numpy as np
import pytest
from osgeo import gdal, ogr, osr
from pytest_mock import MockerFixture
from wps_shared.geospatial.geospatial import rasters_match

from wps_sfms.rasterize_fire_zone_units import (
    default_fire_zone_path,
    main,
    rasterize_fire_zone_units,
)


def create_reference(
    path: Path,
    *,
    columns: int = 3,
    rows: int = 2,
    geotransform: tuple[float, float, float, float, float, float] = (0, 1, 0, 2, 0, -1),
    epsg: int | None = 4326,
) -> None:
    dataset = gdal.GetDriverByName("GTiff").Create(str(path), columns, rows, 1, gdal.GDT_Float32)
    dataset.SetGeoTransform(geotransform)
    if epsg is not None:
        spatial_reference = osr.SpatialReference()
        spatial_reference.ImportFromEPSG(epsg)
        dataset.SetProjection(spatial_reference.ExportToWkt())
    dataset.GetRasterBand(1).SetNoDataValue(-9999)
    dataset.GetRasterBand(1).Fill(1)
    dataset = None


def polygon_wkt(min_x: float, min_y: float, max_x: float, max_y: float) -> str:
    return (
        f"POLYGON (({min_x} {min_y}, {max_x} {min_y}, {max_x} {max_y}, "
        f"{min_x} {max_y}, {min_x} {min_y}))"
    )


def create_fire_zones(
    path: Path,
    polygons: list[tuple[int, str]],
    *,
    epsg: int = 4326,
    field_name: str = "OBJECTID",
    field_type: int = ogr.OFTInteger,
) -> None:
    driver = ogr.GetDriverByName("GeoJSON")
    data_source = driver.CreateDataSource(str(path))
    spatial_reference = osr.SpatialReference()
    spatial_reference.ImportFromEPSG(epsg)
    layer = data_source.CreateLayer("fire_zone_units", spatial_reference, ogr.wkbPolygon)
    layer.CreateField(ogr.FieldDefn(field_name, field_type))

    for object_id, geometry_wkt in polygons:
        feature = ogr.Feature(layer.GetLayerDefn())
        feature.SetField(field_name, object_id)
        feature.SetGeometry(ogr.CreateGeometryFromWkt(geometry_wkt))
        layer.CreateFeature(feature)
        feature = None
    data_source = None


def test_rasterize_matches_reference_grid_and_burns_pixel_centres(tmp_path: Path):
    reference_path = tmp_path / "reference.tif"
    source_path = tmp_path / "zones.geojson"
    output_path = tmp_path / "zones.tif"
    create_reference(reference_path)
    create_fire_zones(
        source_path,
        [
            (7, polygon_wkt(0, 0, 1, 2)),
            (11, polygon_wkt(1, 1, 1.1, 2)),
            (9, polygon_wkt(2, 1, 3, 2)),
        ],
    )
    reference = gdal.Open(str(reference_path), gdal.GA_Update)
    reference.GetRasterBand(1).WriteArray(np.array([[-9999]], dtype=np.float32), 0, 0)
    reference = None

    result = rasterize_fire_zone_units(
        str(reference_path), output_path, source_geojson=str(source_path)
    )

    assert result == output_path
    reference = gdal.Open(str(reference_path))
    output = gdal.Open(str(output_path))
    assert rasters_match(reference, output)
    assert output.GetGeoTransform() == reference.GetGeoTransform()
    assert output.GetProjection() == reference.GetProjection()
    output_band = output.GetRasterBand(1)
    assert output_band.DataType == gdal.GDT_Int32
    assert output_band.GetNoDataValue() == 0
    assert output_band.GetDescription() == "fire_zone_objectid"
    np.testing.assert_array_equal(output_band.ReadAsArray(), [[7, 0, 9], [7, 0, 0]])
    output = None
    reference = None


def test_rasterize_reprojects_fire_zones_to_reference_projection(tmp_path: Path):
    reference_path = tmp_path / "reference_3857.tif"
    source_path = tmp_path / "zones_4326.geojson"
    output_path = tmp_path / "zones_3857.tif"
    create_reference(
        reference_path,
        columns=2,
        rows=2,
        geotransform=(0, 100_000, 0, 200_000, 0, -100_000),
        epsg=3857,
    )
    create_fire_zones(source_path, [(5, polygon_wkt(0, 0, 1, 1))])

    rasterize_fire_zone_units(str(reference_path), output_path, source_geojson=str(source_path))

    output = gdal.Open(str(output_path))
    np.testing.assert_array_equal(output.GetRasterBand(1).ReadAsArray(), [[0, 0], [5, 0]])
    output = None


@pytest.mark.parametrize(
    ("field_name", "field_type", "message"),
    [
        ("ZONE_ID", ogr.OFTInteger, "missing the OBJECTID field"),
        ("OBJECTID", ogr.OFTString, "OBJECTID field must contain integers"),
    ],
)
def test_rasterize_rejects_invalid_objectid_field(
    tmp_path: Path,
    field_name: str,
    field_type: int,
    message: str,
):
    reference_path = tmp_path / "reference.tif"
    source_path = tmp_path / "zones.geojson"
    create_reference(reference_path)
    create_fire_zones(
        source_path,
        [(1, polygon_wkt(0, 0, 1, 1))],
        field_name=field_name,
        field_type=field_type,
    )

    with pytest.raises(ValueError, match=message):
        rasterize_fire_zone_units(
            str(reference_path), tmp_path / "output.tif", source_geojson=str(source_path)
        )


def test_rasterize_rejects_reference_without_projection(tmp_path: Path):
    reference_path = tmp_path / "reference.tif"
    source_path = tmp_path / "zones.geojson"
    create_reference(reference_path, epsg=None)
    create_fire_zones(source_path, [(1, polygon_wkt(0, 0, 1, 1))])

    with pytest.raises(ValueError, match="no coordinate reference system"):
        rasterize_fire_zone_units(
            str(reference_path), tmp_path / "output.tif", source_geojson=str(source_path)
        )


def test_rasterize_requires_overwrite_for_existing_output(tmp_path: Path):
    reference_path = tmp_path / "reference.tif"
    source_path = tmp_path / "zones.geojson"
    output_path = tmp_path / "zones.tif"
    create_reference(reference_path)
    create_fire_zones(source_path, [(1, polygon_wkt(0, 0, 1, 1))])
    output_path.write_bytes(b"existing")

    with pytest.raises(FileExistsError, match="already exists"):
        rasterize_fire_zone_units(str(reference_path), output_path, source_geojson=str(source_path))

    rasterize_fire_zone_units(
        str(reference_path), output_path, source_geojson=str(source_path), overwrite=True
    )
    assert gdal.Open(str(output_path)) is not None


def test_default_fire_zone_path_uses_configured_object_store(mocker: MockerFixture):
    gdal_path = mocker.patch(
        "wps_sfms.rasterize_fire_zone_units.BaseRasterAddresser.gdal_path",
        return_value="/vsis3/test-bucket/zone-units/fire_zone_units.geojson",
    )

    assert default_fire_zone_path() == "/vsis3/test-bucket/zone-units/fire_zone_units.geojson"
    gdal_path.assert_called_once_with("zone-units/fire_zone_units.geojson")


def test_main_passes_cli_arguments_to_rasterizer(tmp_path: Path, mocker: MockerFixture, capsys):
    output_path = tmp_path / "zones.tif"
    rasterize = mocker.patch(
        "wps_sfms.rasterize_fire_zone_units.rasterize_fire_zone_units",
        return_value=output_path,
    )

    assert (
        main(
            [
                "--reference-raster",
                "/vsis3/test/reference.tif",
                "--output-raster",
                str(output_path),
                "--overwrite",
            ]
        )
        == 0
    )

    rasterize.assert_called_once_with(
        "/vsis3/test/reference.tif",
        output_path,
        source_geojson=None,
        overwrite=True,
    )
    assert capsys.readouterr().out == f"Fire zone raster: {output_path}\n"
