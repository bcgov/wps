# Database

To access the local copy of the database, you can shell into it by opening a new terminal window and executing `psql -h localhost -p 5432 -U <db-username>` and enter the local database password when prompted.

### Database Migrations

After making a change to the model, create migration script:

```bash
PYTHONPATH=. alembic revision --autogenerate -m "Comment relevant to change"
```

You may have to modify the generated code to import geoalchemy2

You may want to have a data import/modification step, where you're not actually changing the database, but want to manage new data. You can create an "empty" migration, and insert data as needed:

```bash
PYTHONPATH=. alembic revision -m "Comment relevant to change"
```

Then apply:

```bash
PYTHONPATH=. alembic upgrade head
```

You may need to enable postgis extension:

```sql
CREATE EXTENSION postgis;

```

#### Common Commands

Checking and starting postgres through brew:

```bash
brew services start postgresql
brew services list
```

Shell into local postgres server:

```bash
psql -d postgres
```

Show list of databases:

```psql
\l
```

Connect to 'wps' database:

```psql
\c wps
```

Show list of extensions:

```psql
\dx
```

Install postgis extension:

```psql
create extension postgis;
```

### CrunchyDB Openshift Cluster

The database is deployed using the CrunchyDB postgres operator: https://github.com/CrunchyData/postgres-operator

#### Standby Cluster Restore

To spin up a standby cluster that bootstraps itself from our configured pgbackrest repo run:

`PROJ_TARGET=<your-namespace> BUCKET=<your-bucket> bash openshift/scripts/oc_provision_crunchy_standby.sh <your-suffix> apply`

Further details here: https://access.crunchydata.com/documentation/postgres-operator/latest/tutorials/backups-disaster-recovery/disaster-recovery#repo-based-standby

In the case of needing promote the standby cluster to the primary cluster, follow instructions here: https://access.crunchydata.com/documentation/postgres-operator/latest/tutorials/backups-disaster-recovery/disaster-recovery#promoting-a-standby-cluster
