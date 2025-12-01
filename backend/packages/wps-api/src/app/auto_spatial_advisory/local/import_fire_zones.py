"""
Retrieving fire zones from https://maps.gov.bc.ca/arcserver/rest/services/whse/bcgw_pub_whse_legal_admin_boundaries/MapServer/2
"""
import json
from shapely.geometry import MultiPolygon, Polygon
from shapely import to_geojson, from_geojson
from typing import Final
import asyncio
from app.utils import esri

async def fetch_from_esri():
    # We fetch a list of object id's, fetching the entire layer in one go, will most likely crash
    # the server we're talking to.
    zone_url: Final = "https://maps.gov.bc.ca/arcserver/rest/services/whse/bcgw_pub_whse_legal_admin_boundaries/MapServer/8"
    zone_ids = esri.fetch_object_list(zone_url)
    for object_id in zone_ids:
        # Fetch each object in turn.
        obj = esri.fetch_object(object_id, zone_url)
        for feature in obj.get('features', []):
            attributes = feature.get('attributes', {})
            # Each zone is uniquely identified by a fire zone id.
            mof_fire_zone_id = int(attributes.get('MOF_FIRE_ZONE_ID'))
            geometry = feature.get('geometry', {})
            # Rings???
            # That's right:
            # https://developers.arcgis.com/documentation/common-data-types/geometry-objects.htm
            # "A polygon (specified as esriGeometryPolygon) contains an array of rings or curveRings
            # and a spatialReference."
            rings = geometry.get('rings', [[]])
            polygons = []
            for ring in rings:
                # Simplify each polygon to 1000 meters, preserving topology.
                polygons.append(Polygon(ring).simplify(1000, preserve_topology=True))
            geom = MultiPolygon(polygons)
            geo_json = to_geojson(geom, indent=2)
            data = json.loads(geo_json)
            data['attributes'] = attributes
            with open(f"zone_{mof_fire_zone_id}.geojson", 'w') as f:
                f.write(json.dumps(data))

            with open(f"zone_{mof_fire_zone_id}.geojson", 'r') as f:
                polygon_dict = json.load(f)
                multipolygon = from_geojson(json.dumps(polygon_dict))
                print(multipolygon)
                


if __name__ == '__main__':
    asyncio.run(fetch_from_esri())
