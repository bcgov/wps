# Backup scripts

## backup_to_s3.sh

Bash file that takes a pg_dump and pipes it to gzip and then to s3cmd.

## cleanup_bucket.sh

Bash file that removes all backups as part of pull request cleanup.

## prune.py

Python script that takes a list of backups and removes the oldest ones.

## prune_test.py

Unit tests for prune.py.

## Useful info for local development

### Build the docker image using docker compose

```bash
docker compose build
```

### Run bash in the docker container

```bash
docker compose run --rm backup bash
```

### Run lint and tests locally

```bash
uv sync
make lint
make test
```
