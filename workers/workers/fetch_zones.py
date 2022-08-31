"""

references:
- https://developers.arcgis.com/rest/services-reference/enterprise/query-feature-service-layer-.htm
- https://support.esri.com/en/technical-article/000019645
"""
import os
import json
from typing import Final
from workers.esri import fetch_object_list, fetch_object


def main():
    # We fetch a list of object id's, fetching the entire layer in one go, will most likely crash
    # the server we're talking to.
    zone_url: Final = "https://maps.gov.bc.ca/arcserver/rest/services/whse/bcgw_pub_whse_legal_admin_boundaries/MapServer/8"
    zone_ids = fetch_object_list(zone_url)
    target_folder = 'zones'

    if not os.path.exists(target_folder):
        os.mkdir(target_folder)

    for object_id in zone_ids:
        # Fetch each object in turn.
        target_file = os.path.join(target_folder, f'{object_id}.json')
        if not os.path.exists(target_file):
            obj = fetch_object(object_id, zone_url)
            with open(target_file, 'w') as f:
                # the file being dumped is json, BC Albers EPSG:3005
                json.dump(obj, f)


if __name__ == '__main__':
    main()
