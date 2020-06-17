# Backup templates

These instructions were written using [v2.1.1](https://github.com/BCDevOps/backup-container/releases/tag/2.1.1) of the [BC DevOps backup-container](https://github.com/BCDevOps/backup-container)

## Installation

### Provision a backup PVC

Using the service catalog, provision a backup pvc in each environment.

### OpenShift Build config

Create an imagestream in the tools project:

```bash
oc process -f backup-build.json | oc -n <tools-project> apply -f -
```

Tag the imagestream for use in our different environments:

```bash
oc -n <tools-project> tag backup-postgres:latest backup-postgres:dev
oc -n <tools-project> tag backup-postgres:latest backup-postgres:prod
```

### Deployment config

#### Create a configmap

```bash
oc -n <project> apply -f backup-conf-configmap_DeploymentConfig-<environment>.json
```

#### Create a deployment config

Create a deployment config for backup, with 0 replicas. If you need to do a manual backup, verify
backups, restore or some other maintenance - stop the OpenShift cronjob, increase the number of replicas
to 1, do your maintenance, and reduce the replicas back to 0 when done.

Create a deployment config in your environments (we don't need to use nfs-backup in dev, so you
can override BACKUP_VOLUME_CLASS if desired to be netapp-block-standard - but then be sure not to have
multiple pods access the backup pvc):

```bash
oc -n <project> process -f backup-deploy-<environment>.json -p BACKUP_VOLUME_NAME=<backup volume name> | oc -n <project> apply -f -
```

e.g. for dev:

```bash
oc -n auzhsi-dev process -f backup-deploy-dev.json -p BACKUP_VOLUME_NAME=bk-auzhsi-dev-vgc3svkn4776 -p | oc -n auzhsi-dev apply -f -
```

e.g. for production:

```bash
oc -n auzhsi-prod process -f backup-deploy-prod.json -p BACKUP_VOLUME_NAME=bk-auzhsi-prod-lenk19vmffnx | oc -n auzhsi-prod apply -f -
```

#### Test your deployment

Scale up (note that a backup will be made on startup):

```bash
oc -n <project> scale dc/backup-postgres --replicas=1
```

e.g. for production:

```bash
oc -n auzhsi-prod scale dc/backup-postgres --replicas=1
```

Rsh, backup and validate:

```bash
oc -n <project> rsh <pod>
# List existing configuration:
./backup.sh -c
# Perform a single backup and exit
./backup -1
# List existing backups:
./backup.sh -l
```

Scale back down:

```bash
oc -n <project> scale dc/backup-postgres --replicas=0
```

#### Set up openshift cronjob

Create the cronjob:

```bash
oc process -f backup-cronjob.yaml -p IMAGE_NAMESPACE=<tools-project> -p TAG_NAME=<dev/prod> \
    -p DATABASE_SERVICE_NAME=<name of service> -p DATABASE_NAME=<name of database> \
    -p DATABASE_DEPLOYMENT_NAME=<name of deployment> | oc -n <project> apply -f -
```

e.g. - dev:

```bash
oc process -f backup-cronjob.yaml -p IMAGE_NAMESPACE=auzhsi-tools -p TAG_NAME=dev \
    -p DATABASE_SERVICE_NAME=psufiderdev-postgresql -p DATABASE_NAME=psufiderdev \
    -p DATABASE_DEPLOYMENT_NAME=psufiderdev-postgresql | oc -n auzhsi-dev apply -f -
```

e.g. - prod:

````bash
oc process -f backup-cronjob.yaml -p TAG_NAME=prod -p DATABASE_SERVICE_NAME=psufider-postgresql -p DATABASE_NAME=psufider -p DATABASE_DEPLOYMENT_NAME=psufider-postgresql | oc -n auzhsi-prod apply -f -

##### Validate cronjob

Some useful commands:

```bash
# List your cronjobs - you should see the one you've created.
oc -n <project> get cronjobs
# Get cronjob details.
oc -n <project> describe cronjob backup-postgres
# Patch the cronjob to run more frequently (every 5 minutes).
oc -n <project> patch cronjob backup-postgres -p '{ "spec": { "schedule": "*/5 * * * *" } }'
# Patch the cronjob back to running at 1am once a day.
oc -n <project> patch cronjob backup-postgres -p '{ "spec": { "schedule": "0 1 * * *" } }'
# Debug a recently run pod
oc -n <project> debug <pod>
````

## Atribution

These templates taken from the [BC DevOps backup-container](https://github.com/BCDevOps/backup-container)
and modified for this project.
