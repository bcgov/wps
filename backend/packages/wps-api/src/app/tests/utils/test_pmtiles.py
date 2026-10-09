import json
import struct

import numpy as np
from osgeo import gdal, ogr, osr
from wps_shared.geospatial.polygonize import polygonize_in_memory

from app.auto_spatial_advisory.classify_hfi import classify_hfi
from app.utils.pmtiles import write_empty_pmtiles, write_geojson


def test_write_geojson_reprojects_all_features(tmp_path):
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(3005)
    data_source = ogr.GetDriverByName("Memory").CreateDataSource("")
    layer = data_source.CreateLayer("hfi", srs, ogr.wkbPolygon)
    layer.CreateField(ogr.FieldDefn("hfi", ogr.OFTInteger))
    for i in range(3):
        feature = ogr.Feature(layer.GetLayerDefn())
        feature.SetField("hfi", i)
        x = 1000000 + i * 1000
        feature.SetGeometry(
            ogr.CreateGeometryFromWkt(
                f"POLYGON(({x} 1000000,{x + 500} 1000000,{x + 500} 1000500,{x} 1000000))"
            )
        )
        layer.CreateFeature(feature)

    geojson_path = write_geojson(layer, str(tmp_path))

    with open(geojson_path) as f:
        geojson = json.load(f)
    assert [feature["properties"]["hfi"] for feature in geojson["features"]] == [0, 1, 2]
    lon, lat = geojson["features"][0]["geometry"]["coordinates"][0][0]
    assert -140 < lon < -110 and 45 < lat < 61


def test_hfi_below_advisory_polygonizes_to_no_features(tmp_path):
    hfi_path = str(tmp_path / "hfi.tif")
    ds = gdal.GetDriverByName("GTiff").Create(hfi_path, 4, 4, 1, gdal.GDT_Float32)
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(3005)
    ds.SetProjection(srs.ExportToWkt())
    ds.SetGeoTransform((1000000, 2000, 0, 1000000, 0, -2000))
    ds.GetRasterBand(1).WriteArray(np.array([[3911.9, -102, 0, 100]] * 4, dtype=np.float32))
    ds = None
    classified_path = str(tmp_path / "classified.tif")

    classify_hfi(hfi_path, classified_path)

    with polygonize_in_memory(classified_path, "hfi", "hfi") as layer:
        assert layer.GetFeatureCount() == 0


def test_write_empty_pmtiles(tmp_path):
    path = tmp_path / "empty.pmtiles"
    write_empty_pmtiles(str(path), min_zoom=4, max_zoom=11)
    data = path.read_bytes()

    magic, version, root_offset, root_length, metadata_offset, metadata_length = struct.unpack_from(
        "<7sB4Q", data
    )
    tile_data_offset, tile_data_length = struct.unpack_from("<2Q", data, 56)
    assert (magic, version) == (b"PMTiles", 3)
    assert data[100:102] == bytes([4, 11])
    # one root entry, pointing at the only tile
    assert data[root_offset : root_offset + root_length] == bytes([1, 0, 1, tile_data_length, 1])
    metadata = json.loads(data[metadata_offset : metadata_offset + metadata_length])
    assert metadata["vector_layers"][0]["id"] == "hfi"
    assert tile_data_offset + tile_data_length == len(data)


def test_empty_pmtiles_is_readable_as_pmtiles(tmp_path):
    path = str(tmp_path / "empty.pmtiles")
    write_empty_pmtiles(path)

    data_source = gdal.OpenEx(path, gdal.OF_VECTOR)

    assert data_source.GetDriver().ShortName == "PMTiles"
    layer = data_source.GetLayerByName("hfi")
    assert layer.GetFeatureCount() == 0
