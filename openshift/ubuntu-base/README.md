# Ubuntu base image.

This image is currently only needed for the c-haines cronjob, as it uses a more up to date version of gdal
that is available in the api.

## Apply template to build the base image on Openshift.

```bash
oc -n e1e498-tools process -f build.yaml | oc -n e1e498-tools apply -f -
bash
```

## The image can also be built locally, and then pushed to Openshift.

```bash
# build your docker image
docker build --tag=ubuntu-base:20.04 .
# tag it for upload
docker tag ubuntu-base:20.04 image-registry.openshift-image-registry.svc:5000/e1e498-tools/ubuntu-base:20.04
# log in to openshift docker
docker login -u developer -p $(oc whoami -t) image-registry.apps.silver.devops.gov.bc.ca
# push it
docker tag ubuntu-base:20.04 image-registry.openshift-image-registry.svc:5000/e1e498-tools/ubuntu-base:20.04
```
