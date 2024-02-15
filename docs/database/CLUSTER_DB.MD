# Cluster Database

## Overview

The diagram below shows an overview of the database cluster. The components circled in red are the pieces we use operationally at the time of writing.

![Cluster Architecture Overview](cluster-overview.png)
Source: https://access.crunchydata.com/documentation/postgres-operator/latest/architecture

## Components

- `Primary` Postgres instance

  - The primary postgres database that replica instances replicate from

- `Replica` Postgres instances

  - Replicas stream WAL logs from the primary to keep themselves up to date as data changes occur

- `pgbackrest`

  - This runs in a container alongside the postgres database and pushes WAL archives to the S3 repo. The wal logs enable bootstrapping of new clusters as well as backups.

  - Backup specific configuration is declared in [crunchy.yaml](../../openshift/templates/crunchy.yaml), notably:

    - The `path` to the archive/backup is specified as /`pgbackrest/${SUFFIX}/repo1`
    - **Full Backup**: scheduled weekly on Sunday at 1am
    - **Differential Backup**: taken daily at 1am, except on Sundays
    - **Manual Backup**: are enabled through the `manual` configured property

      - **Trigger a manual backup**, by annotating the primary cluster with: `kubectl annotate -n <namespace-license-plate> postgrescluster <postgres-cluster> --overwritepostgres-operator.crunchydata.com/pgbackrest-backup="$( date '+%F\_%H:%M:%S' )"`

    - To see the status of a backup look in the condition block of the result of`oc describe postgrescluster <postgres-cluster>`, e.g.:

            Last Transition Time:  2024-02-13T23:51:47Z
            Message:               Manual backup completed successfully
            Observed Generation:   16
            Reason:                ManualBackupComplete
            Status:                True
            Type:                  PGBackRestManualBackupSuccessful

## Disaster Recovery (DR)

In the rare case where the multi-instance primary cluster is unrecoverable a repo-based standby cluster can be spun up and bootstrapped from the S3 archive repo.

![Repo-based Standby Architecture](repo-standby-overview.png)
Source: https://access.crunchydata.com/documentation/postgres-operator/latest/architecture/disaster-recovery#repo-based-standby

When the repo-standby is spun, it reads and applies the WAL in order to replicate the state of the database and runs as it's own cluster, separate from the primary.

Spin up the Repo-Standby Cluster with:
`PROJ_TARGET=<namespace-license-plate> BUCKET=<s3-bucket> bash openshift/scripts/oc_provision_crunchy_standby.sh <suffix> apply`

- Anecdotally, spinning up a standby cluster for a 15GB database took about 5 minutes

### Promoting a Standby Cluster

Once a standby is stood up, it can be promoted to be the primary cluster. **Note: only do this if the existing primary has been shut down first.**

Promote the standby cluster by editing the [crunchy_standby.yaml](../../openshift/templates/crunchy_standby.yaml) to set the `standby` field to `false`.

More details here: https://access.crunchydata.com/documentation/postgres-operator/latest/architecture/disaster-recovery#promoting-a-standby-cluster
