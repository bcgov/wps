# Patroni for Openshift - with PostGIS for the Wildfire Predictive Services Unit

The WPS project uses an image based on the bcgov patroni image (see: https://github.com/bcgov/patroni-postgres-container),
adding PostGIS (see: https://github.com/postgis/docker-postgis/).

## Usage in the WPS project

The WPS pipeline currently assumes the existence of an appropriately tagged patroni-postgres imagestream in the tools project.

### Build and tag an imagestream as follows:

```bash
# Build a patroni imagestream:
oc -n e1e498-tools process -f openshift/build.yaml | oc -n e1e498-tools apply -f -
# Tag the old imagestream so we can keep it around if we need to revert:
oc -n e1e498-tools tag patroni-postgres:v12 patroni-postgres:v12-<date deprecated, e.g. 20200826>
# Tag the new imagestream (it won't be used until the pods get re-created):
oc -n e1e498-tools tag patroni-postgres:v12-latest patroni-postgres:v12
```

#### Common build failures

```text
E: Version '3.1.0+dfsg-1.pgdg90+1' for 'postgresql-11-postgis-3' was not found
E: Version '3.1.0+dfsg-1.pgdg90+1' for 'postgresql-11-postgis-3-scripts' was not found
```

The latest version of the POSTGIS_VERSION available on debian is constantly changing. It is very likely, that when you attempt to build the image,
it will fail because the version of postgis has changed. The most sure fire way of establishing which version to use is to:

```bash
git clone git@github.com:postgis/docker-postgis.git
cd docker-postgis
./update.sh
git status
# look if 11-3.1/Dockerfile has changed - see what's the latest:
git diff 11-3.1/Dockerfile
```

#### Other examples of building and tagging

```bash
# Build a patroni imagestream, override the git branch:
oc -n e1e498-tools process -f openshift/build.yaml -p GIT_REF="yourbranchnamehere"  | oc -n e1e498-tools apply -f -
```

### Allow the production product to pull images from tools

```bash
oc -n e1e498-prod policy add-role-to-user \
    system:image-puller system:serviceaccount:e1e498-prod:patroniocp-wps-prod \
    --namespace=e1e498-tools
```

## More examples

```bash
# Build the patroni image, specifying some of the variables (useful if you're testing)
oc -n e1e498-tools process -f openshift/build.yaml -p GIT_REF=mybranch -p VERSION=yourtag | oc -n e1e498-tools apply -f -
```

## Upgrade issues

Upgrades to the version of PostGIS in the patroni image, don't mean that the database plugins are upgraded. You need to run the following SQL to upgrade the database plugins:

```bash
SELECT postgis_extensions_upgrade();
```

This script cannot be run as part of the alembic scripts in the api project, the api uses a `wps` user that does not have the appropriate priveleges. Upgrading the image may this require manually running `SELECT postgis_extensions_upgrade();` on the target database once the new image has been applied.

The PostGIS version can be checked with `SELECT postgis_full_version();`