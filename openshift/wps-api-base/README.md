# unicorn base image

The Docker image and template in this folder are used to create the base image used in the api build.

- Using this base image can save some time, as it installs some various packages that take a long time
  to install and don't change often, such as GDAL, R and CFFDRS.

## apply template

```bash
oc -n e1e498-tools process -f build.yaml | oc -n e1e498-tools apply -f -
```

## apply template using a specified branch

```bash
oc -n e1e498-tools -p GIT_BRANCH=my-branch process -f build.yaml | oc -n e1e498-tools apply -f -
```

## The image can also be built locally, and then pushed to Openshift

```bash
# build your docker image
docker build --tag=wps-api-base:python3.8 .
# tag it for upload
docker tag wps-api-base:python3.8 image-registry.openshift-image-registry.svc:5000/e1e498-tools/wps-api-base:python3.8
# log in to openshift docker
docker login -u developer -p $(oc whoami -t) image-registry.apps.silver.devops.gov.bc.ca
# push it
docker push image-registry.apps.silver.devops.gov.bc.ca/e1e498-tools/wps-api-base:python3.8
```
