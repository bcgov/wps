# S3 Backup Image

Uses the official Debian-based postgres 16 image (https://hub.docker.com/_/postgres) so `pg_dump` matches the database's major version.
Installs the AWS CLI, and the Python dependencies for `prune.py` with uv.
Copies and runs the driver script.

## Building and deploying

The image is built and promoted the same way as the `api`, `web` and `jobs` images:

- Each pull request builds `wps-s3-backup-pr-###:pr-###` in `e1e498-tools` from [`openshift/build.yaml`](openshift/build.yaml) (the `build-image` job in `.github/workflows/deployment.yml`).
- The pull request's dev backup cronjob (`backup-postgres-wps-pr-###`) runs that image against the pull request's database.
- Deploying to production promotes it to `wps-s3-backup-prod:prod`, which the production backup cronjob and the pull request S3 cleanup job use.

### Run a backup in dev on demand

```bash
oc -n e1e498-dev create job --from=cronjob/backup-postgres-wps-pr-### backup-test
oc -n e1e498-dev logs -f job/backup-test
oc -n e1e498-dev delete job/backup-test
```

### Roll back production

`oc_promote.sh` keeps the last 5 promoted tags on `wps-s3-backup-prod`. To roll back, point `prod` at an earlier one:

```bash
oc -n e1e498-tools get is/wps-s3-backup-prod
oc -n e1e498-tools tag wps-s3-backup-prod:pr-### wps-s3-backup-prod:prod
```
