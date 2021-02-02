# Backup templates

These instructions were written referencing [v2.1.1](https://github.com/BCDevOps/backup-container/releases/tag/2.1.1) of the [BC DevOps backup-container](https://github.com/BCDevOps/backup-container), for full reference, refer to the [backup container README](https://github.com/BCDevOps/backup-container/blob/master/README.md).

## Installation

### Provision a backup PVC

Using the service catalog, provision a backup pvc in each environment.

### OpenShift Build config

Create an imagestream in the tools project:

```bash
oc process -f backup-build.json | oc -n <tools-project> apply -f -
```

```bash
oc process -f backup-build.json -p NAME=backup-mariadb -p DOCKER_FILE_PATH=Dockerfile_MariaDB | oc -n <tools-project> apply -f -
```

Tag the imagestream for use in our different environments:

```bash
oc -n <tools-project> tag backup-postgres:latest backup-postgres:dev
oc -n <tools-project> tag backup-postgres:latest backup-postgres:prod
```

### Deployment config

#### Create a configmap

The long running backup-container pod needs this configuration.

```bash
oc -n <project> apply -f backup-conf-configmap_DeploymentConfig-<environment>.json
```

For instructions on how to generate the configuration file, refer to [backup-container README](https://github.com/BCDevOps/backup-container/tree/2.1.1#backupconf)

#### Create a deployment config

Create a deployment config for backup, with 0 replicas. If you need to do a manual backup, verify
backups, restore or some other maintenance - stop the OpenShift cronjob, increase the number of replicas
to 1, do your maintenance, and reduce the replicas back to 0 when done.

Create a deployment config in your environments (we don't need to use nfs-backup in dev, so you
can override BACKUP_VOLUME_CLASS if desired to be netapp-block-standard - but then be extra sure not to have
multiple pods access the backup pvc):

```bash
oc -n <project> process -f backup-deploy-<environment>.json -p BACKUP_VOLUME_NAME=<backup volume name> | oc -n <project> apply -f -
```

#### Test your deployment

Scale up (note: a backup will be made on startup):

```bash
oc -n <project> scale dc/backup-postgres --replicas=1
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

### Set up openshift cronjob

Create the cronjob:

```bash
oc process -f backup-cronjob.yaml -p IMAGE_NAMESPACE=<tools-project> -p TAG_NAME=<dev/prod> \
    -p DATABASE_SERVICE_NAME=<name of service> -p DATABASE_NAME=<name of database> \
    -p DATABASE_DEPLOYMENT_NAME=<name of deployment> \
    -p JOB_PERSISTENT_STORAGE_NAME=<name of backup volume> \
    -p JOB_NAME=<a good name for the cronjob> | oc -n <project> apply -f -
```

e.g.:

```bash
oc process -f backup-cronjob.yaml -p IMAGE_NAMESPACE=auzhsi-tools -p TAG_NAME=prod \
    -p DATABASE_SERVICE_NAME=patroni-leader-wps-prod -p DATABASE_NAME=wps-prod \
    -p DATABASE_DEPLOYMENT_NAME=wps-prod \
    -p DATABASE_USER_KEY_NAME=app-db-username \
    -p DATABASE_PASSWORD_KEY_NAME=app-db-password \
    -p JOB_PERSISTENT_STORAGE_NAME=<name of backup volume> \
    -p JOB_NAME=backup-wps-prod | oc -n auzhsi-prod apply -f -
```

#### Validate cronjob

Some useful commands:

```bash
# List your cronjobs - you should see the one you've created:
oc -n <project> get cronjobs
# Get cronjob details:
oc -n <project> describe cronjob <cronjob name>
# Patch the cronjob to run more frequently (every 5 minutes):
oc -n <project> patch cronjob <cronjob name> -p '{ "spec": { "schedule": "*/5 * * * *" } }'
# Patch the cronjob back to running at 1am once a day:
oc -n <project> patch cronjob <cronjob name> -p '{ "spec": { "schedule": "0 1 * * *" } }'
# Debug a recently run pod:
oc -n <project> debug <pod>
```

### Restore

- Scale down any applications using the database.

```bash
oc -n <project> scale dc/<your app using the db you want to restore> --replicas=0
```

- Scale up the backup dc.

```bash
oc -n <project> scale dc/<your backup dc> --replicas=1
```

- Rsh to the backup pod

```bash
oc -n <project> rsh <pod>
# List the backups.
./bash.sh -l
```

- Follow instructions from [backup.usage](https://github.com/BCDevOps/backup-container/blob/master/docker/backup.usage). Note that in order to restore the postgres admin password is required. You may have to set one manualy.

```bash
# the basic form for a restore:
./bash -r <database to restore to> -f <filename to restore>
```

- Setting the admin password if you need to:

```bash
# rsh to db pod.
oc -n <project> rsh <pod>
# start psql
psql
# change the password
\password
```

## Attribution

The templates in this folder taken from the [BC DevOps backup-container project](https://github.com/BCDevOps/backup-container) and modified for this project.
