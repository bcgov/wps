# S3 Backup Image

Uses postgres-12, centos base image: https://hub.docker.com/r/centos/postgresql-12-centos7
Installs single dependency, the AWS cli.
Copys and runs driver script

## Building

### Apply template to build the base image on Openshift

```bash
oc -n e1e498-tools process -f build.yaml | oc -n e1e498-tools apply -f -
```

### Apply template using a specified branch and version

```bash
oc -n e1e498-tools -p VERSION=some-date -p GIT_BRANCH=my-branch process -f build.yaml | oc -n e1e498-tools apply -f -
```

### Kick off the build

```bash
oc -n e1e498-tools start-build s3-backup --follow
```

### Re-tag for production

Assuming you've built an image tagged for dev, you may now want to tag it for production. Remember to retain
the current prod image in case you want to revert!

You may also want to delete any old tags that are no longer relevant.

```bash
# maybe tag the current production image in case we need to revert
oc -n e1e498-tools tag s3-backup:prod s3-backup:previous-prod
# tag this image with something useful, may todays date
oc -n e1e498-tools tag s3-backup:dev s3-backup:some-sensible-tag-like-the-current-date
# tag it for production
oc -n e1e498-tools tag s3-backup:dev s3-backup:prod
```
