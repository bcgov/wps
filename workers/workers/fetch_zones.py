import json
from typing import Final
from workers.esri import fetch_object_list, fetch_object


def main():
    # We fetch a list of object id's, fetching the entire layer in one go, will probably crash the
    # server.
    zone_url: Final = "https://maps.gov.bc.ca/arcserver/rest/services/whse/bcgw_pub_whse_legal_admin_boundaries/MapServer/8"
    zone_ids = fetch_object_list(zone_url)

    for object_id in zone_ids:
        # Fetch each object in turn.
        obj = fetch_object(object_id, zone_url)
        with open(f'zones/{object_id}.json', 'w') as f:
            json.dump(obj, f)


if __name__ == '__main__':
    main()
