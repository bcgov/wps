# WPS API Base Image

The Docker image and template in this folder are used to create the base image used in the api build.

Using this base image can save some time, as it installs some various packages that take a long time
to install and don't change often, such as GDAL, `wkhtmltopdf`, and `tippecanoe`.

The image is published to GHCR by GitHub Actions from [`.github/workflows/publish_docker_base.yml`](../../.github/workflows/publish_docker_base.yml).

- Triggered on pushes to `main`
- Can also be run manually with `workflow_dispatch`
  - `gh workflow run "Publish Base Docker Image to GHCR" --ref <branch-name>`
- Publishes `ghcr.io/bcgov/wps/wps-api-base:<mm-dd-yyyy>`
- Also updates `ghcr.io/bcgov/wps/wps-api-base:latest`

## Local Build

To build the image locally:

```bash
docker build -f openshift/wps-api-base/docker/Dockerfile -t wps-api-base:local .
```

## OpenShift Build

The OpenShift template is still included in case we ever need to build this image in OpenShift instead of GitHub Actions.

```bash
oc -n e1e498-tools process -f openshift/wps-api-base/openshift/build.yaml | oc -n e1e498-tools apply -f -
```

### apply template using a specified branch and version

```bash
oc -n e1e498-tools process \
  -p GIT_BRANCH=my-branch \
  -p VERSION=01-01-2025 \
  -f openshift/wps-api-base/openshift/build.yaml | oc -n e1e498-tools apply -f -
```

### The image can be built by kicking off a build in Openshift

```bash
oc -n e1e498-tools start-build wps-api-base --follow

# now tag the built image as prod
oc -n e1e498-tools tag wps-api-base:<dd-mm-yyyy> wps-api-base:ubuntu.24.04-latest
```
