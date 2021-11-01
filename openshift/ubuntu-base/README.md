# Ubuntu base image

This image is currently only needed for the c-haines cronjob, as it uses a more up to date version of gdal
than is available in the api.

## Apply template to build the base image on Openshift

```bash
oc -n e1e498-tools process -f build.yaml | oc -n e1e498-tools apply -f -
```

## Apply template using a specified branch

```bash
oc -n e1e498-tools -p GIT_BRANCH=my-branch process -f build.yaml | oc -n e1e498-tools apply -f -
```

## The image can also be built locally, and then pushed to Openshift

```bash
# build your docker image
docker build . --tag=ubuntu-base:my-tag .
# tag it for upload
docker tag ubuntu-base:my-tag image-registry.apps.silver.devops.gov.bc.ca/e1e498-tools/ubuntu-base:my-tag
# log in to openshift docker
docker login -u developer -p $(oc whoami -t) image-registry.apps.silver.devops.gov.bc.ca
# push it
docker push image-registry.apps.silver.devops.gov.bc.ca/e1e498-tools/ubuntu-base:my-tag
# once you're good to go
oc -n e1e498-tools tag ubuntu-base:my-tag ubuntu-base:20.04
```
