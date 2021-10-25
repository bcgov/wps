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

### MacOS specific instructions

If you have trouble getting poetry to use python 3.6.8, reference this [StackOverflow post](https://stackoverflow.com/questions/66482346/problems-installing-python-3-6-with-pyenv-on-mac-os-big-sur):

```bash
brew update
brew upgrade
CFLAGS="-I$(brew --prefix openssl)/include -I$(brew --prefix bzip2)/include -I$(brew --prefix readline)/include -I$(xcrun --show-sdk-path)/usr/include" LDFLAGS="-L$(brew --prefix openssl)/lib -L$(brew --prefix readline)/lib -L$(brew --prefix zlib)/lib -L$(brew --prefix bzip2)/lib" pyenv install --patch 3.6.8 < <(curl -sSL https://github.com/python/cpython/commit/8ea6353.patch\?full_index\=1)
brew reinstall zlib bzip2
poetry env use /Users/[user]/.pyenv/versions/3.6.8/bin/python
poetry install
```
