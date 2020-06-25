# Patroni for Openshift - with PostGIS for the Wildfire Predictive Services Unit

## Source & Credit

Copied from [BCDevOps](https://github.com/bcdevOps/platform-services/) which was in turn sourced from [Patroni](https://github.com/zalando/patroni) and modified for PostGIS with assistence from [Stephen Hillier](https://gist.github.com/stephenhillier/17bf0a7365f00c916d80733028f34ae9).

## Modifications made

- Dockerfile and post_init.sh modified to include PostGIS.
- post_init.sh modified to escape username and database.

## Usage in the WPS project

The WPS pipeline currently assumes the existence of an appropriately tagged patroni imagestream in the tools project.

Build and tag an imagestream as follows:

```bash
# Build a patroni imagestream:
oc -n auzhsi-tools process -f openshift/build.yaml | oc -n auzhsi-tools apply -f -
# Tag the imagestream:
oc -n auzhsi-tools tag patroni:v10-latest patroni:10
```
