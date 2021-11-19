# Vector tile server

## Get the data

### Fire Zones

https://maps.gov.bc.ca/arcserver/rest/services/whse/bcgw_pub_whse_legal_admin_boundaries/MapServer/8

https://maps.gov.bc.ca/arcserver/rest/services/whse/bcgw_pub_whse_legal_admin_boundaries/MapServer/8/query?where=objectid%3=1000&f=json

see: scripts/fetch_feature_layer.py

```

```

## Put date in DB

## Configure pg_tile server

Docker sucks when it needs to connect to localhost - so:

```bash
mkdir pg_tileserv
cd pg_tileserv
wget https://postgisftw.s3.amazonaws.com/pg_tileserv_latest_linux.zip
unzip pg_tileserv
export DATABASE_URL=postgresql://wps:wps@localhost/wps
./pg_tileserv
```

## Serve up data

## Review process to keep data up to date
