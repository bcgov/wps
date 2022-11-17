# wps-tileserver

Vector tile server for the Wildfire Predictive Services Unit

[![Lifecycle:Experimental](https://img.shields.io/badge/Lifecycle-Experimental-339999)](https://github.com/bcgov/repomountie/blob/master/doc/lifecycle-badges.md)

## Overview

The intention of this project is to:

- provide tools to easily spin up a vector tile server in openshift, in a project agnostic manner.
- provide tools to manually pull data from an esri arc server into a postgis database.
- provide tools that periodically synchronize data from an esri arc server into postgis.

### Components

- postgis database server. (it is assumed you have a working postgis database server)
- pg_tileserv - serves up vector tiles from postgis server.
- proxy server (varnish?) - caches responses.
- sync cronjob - updates database periodically.

### Reference

https://blog.crunchydata.com/blog/production-postgis-vector-tiles-caching
https://github.com/CrunchyData/pg_tileserv

## Local development

### Assumptions

- postgresql server with postgis running locally

### Configure pg_tile server

Download the latest [pg_tileserver](https://github.com/CrunchyData/pg_tileserv), unzip and start.

```bash
mkdir pg_tileserv
cd pg_tileserv
wget https://postgisftw.s3.amazonaws.com/pg_tileserv_latest_linux.zip
unzip pg_tileserv
export DATABASE_URL=postgresql://tileserv:tileserv@localhost/tileserv
./pg_tileserv
```

### Install python requirements

_This step only required if you're going to be using the python scripts in this repo to load data. If you're loading directly from shapefiles, then skip this step._

#### Assumptions

- appropriate python version is installed
- [python poetry](https://python-poetry.org/) is installed

#### Install python requirements

```bash
poetry install
```

## Loading data

### Create a user and database for your tileserver

```sql
create user tileserv with password 'tileserv';
create database tileserv with owner tileserv;
\c tileserv
CREATE EXTENSION IF NOT EXISTS postgis;
```

### Using an arcserver rest endpoint

Given some arcserver layer endpoint, e.g.: [Fire Zones](https://maps.gov.bc.ca/arcserver/rest/services/whse/bcgw_pub_whse_legal_admin_boundaries/MapServer/8) or [Fire Centres](https://maps.gov.bc.ca/arcserver/rest/services/whse/bcgw_pub_whse_legal_admin_boundaries/MapServer/2)

Use the `fetch_feature_layer.py` helper script:

```bash
poetry run python fetch_feature_layer.py --help
```

e.g.:

```bash
poetry run python fetch_feature_layer.py https://maps.gov.bc.ca/arcserver/rest/services/whse/bcgw_pub_whse_legal_admin_boundaries/MapServer/8 localhost tileserv tileserv tileserv fire_zones
```

### Using a shapefile

-nlt <type> Define the geometry type for the created layer
-lco NAME=VALUE Layer creation option (format specific)
-nln <name> Assign an alternate name to the new layer
-overwrite Delete the output layer and recreate it empty

```bash
ogr2ogr -f "PostgreSQL" PG:"dbname=tileserv host=localhost user=tileserv password=tileserv" "my_shapefile.shp" -nlt MULTIPOLYGON -lco precision=NO -nln fire_area_thessian_polygons -overwrite
```

_note_ - special characters in the ogr2ogr password string can be escaped with a backslash.

## Deploy

### Assumptions

- You have the oc command line installed and you're logged in.
- You have docker installed locally.
- You have a postgres database in your target openshift environment that can be accessed by pg_tileserv (you made need to add additional rules to allow your tile server to communicate with your database.)

### Instructions

#### Prepare your openshift environment

```bash
# we have docker limits, so pull the pg_tileserv images locally - then put them in openshift

# pull local
docker pull pramsey/pg_tileserv

# tag for upload
docker tag pramsey/pg_tileserv image-registry.apps.silver.devops.gov.bc.ca/e1e498-tools/pg_tileserv:latest

# log in to openshift docker
docker login -u developer -p $(oc whoami -t) image-registry.apps.silver.devops.gov.bc.ca

# push it
docker push image-registry.apps.silver.devops.gov.bc.ca/e1e498-tools/pg_tileserv:latest

# prepare nginx - creating a build configuration
# note: for some reason specifying the tag for nginx will result in an image that doesn't support s2i
oc new-build nginx~[git hub repository] --context-dir=[folder with nginx config] --name=[name of buildconfig and imagestream]
# e.g.: oc -n e1e498-tools new-build nginx~https://github.com/bcgov/wps-vector-tileserver.git --context-dir=openshift --name=nginx-tilecache
```

#### Deploy pg_tileserver

```bash
# deploy pg_tileserv
oc -n e1e498-dev process -f tileserv.yaml | oc -n e1e498-dev apply -f -
```

### Manually Loading data into your openshift hosted postgis database

The easiest way to achieve this, is to tunnel to your database server and then run the import scripts as if your database was local.

```bash
oc port-forward patroni-wps-mapserver-prototype-1 5432:5432
```
