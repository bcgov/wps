# S3 Backup Image

Uses postgres-12, centos base image: https://hub.docker.com/r/centos/postgresql-12-centos7
Installs single dependency, s3cmd: https://github.com/s3tools/s3cmd
Copys and runs driver script

## Building

### Apply template to build the base image on Openshift

```bash
oc -n e1e498-tools process -f build.yaml | oc -n e1e498-tools apply -f -
```

### Apply template using a specified branch

```bash
oc -n e1e498-tools -p GIT_BRANCH=my-branch process -f build.yaml | oc -n e1e498-tools apply -f -
```
