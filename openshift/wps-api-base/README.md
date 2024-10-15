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
oc -n e1e498-tools process -p GIT_BRANCH=my-branch process -f build.yaml | oc -n e1e498-tools apply -f -
```

## The image can also be built by kicking off a build in Openshift

```bash
# dry run to check first
VERSION=<dd-mm-yyyy> oc_build.sh

# then run
VERSION=<dd-mm-yyyy> oc_build.sh apply

# now tag the built image as prod
oc -n e1e498-tools tag wps-api-base:<dd-mm-yyyy> wps-api-base:ubuntu.24.04-latest
```
