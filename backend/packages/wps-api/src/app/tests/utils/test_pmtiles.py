import json

from osgeo import ogr, osr

from app.utils.pmtiles import write_geojson


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
            ogr.CreateGeometryFromWkt(f"POLYGON(({x} 1000000,{x + 500} 1000000,{x + 500} 1000500,{x} 1000000))")
        )
        layer.CreateFeature(feature)

    geojson_path = write_geojson(layer, str(tmp_path))

    with open(geojson_path) as f:
        geojson = json.load(f)
    assert [feature["properties"]["hfi"] for feature in geojson["features"]] == [0, 1, 2]
    lon, lat = geojson["features"][0]["geometry"]["coordinates"][0][0]
    assert -140 < lon < -110 and 45 < lat < 61
