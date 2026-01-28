# wps-jobs-base image

The Docker image and template in this directory are used to create the base image used in the wps_jobs build.

- Using this base image can save some time, as it installs some various packages that take a long time to install and don't change often, such as GDAL.

## working in dev

Update the build config with your GIT_BRANCH and VERSION.

```bash
oc -n e1e498-tools process -p GIT_BRANCH=my-branch process -p VERSION=dd-mm-yyyy -f ./openshift/build.yaml | oc -n e1e498-tools apply -f -
```

Kick off a build

```bash
oc -n e1e498-tools start-build wps-jobs-base --follow
```

## imagestream management

Once you are happy with your changes to the wps-jobs-base image, tag the current prod image as prod-old just in case.

```bash
oc -n e1e498-tools tag wps-jobs-base:prod wps-jobs-base:old-prod
```

Now tag the new image you are happy with as prod

```bash
oc -n e1e498-tools tag wps-jobs-base:dev wps-jobs-base:prod
```
