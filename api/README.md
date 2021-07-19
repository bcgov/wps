# Wildfire Predictive Services Unit FWI Percentile Calculator API

## Description

Wildfire Predictive Services Unit support decision making in prevention, preparedness, response and recovery.

## Getting Started

### Dependencies

- Docker [Mac](https://hub.docker.com/editions/community/docker-ce-desktop-mac/), [Win](https://hub.docker.com/editions/community/docker-ce-desktop-windows/), [Ubuntu](https://docs.docker.com/install/linux/docker-ce/ubuntu/), [Fedora](https://docs.docker.com/install/linux/docker-ce/fedora/)

- Docker Compose

```bash
brew install docker-compose
```

OR

```
pip install docker-compose
```

### Installing

You will need an environment file. See: .env.example.

#### Local machine, in docker

For local development, you can copy .env.example to .env.docker.

```bash
docker-compose build
```

#### Local machine, running MacOS

For local development, you can copy .env.example to .env.

NOTE: matching the version of postgresql, postgis and gdal with production is problematic, and best
avoided. (postgresql + postgis binaries on mac use a newer version of gdal that we don't have on debian yet.)

NOTE: installing postgresql, postgis and gdal as binaries is the preffered method of installation,
instructions for installing from source are included for reference.

##### Postgresql - from source

```bash
./configure
make
sudo make install

# create a user for postgres
sudo dscl . -create /Users/postgres
sudo dscl . -create /Users/postgres UserShell /bin/bash
sudo dscl . -create /Users/postgres RealName Postgresql
sudo dscl . -create /Users/postgres UniqueID `dscl . -list /Users UniqueID | awk '{print $2 + 1}' | sort -n | tail -1`
sudo dscl . -create /Users/postgres NFSHomeDirectory /usr/local/pgsql

# grant user rights, create database
sudo chown postgres /usr/local/pgsql/data
sudo -u postgres /usr/local/pgsql/bin/initdb -D /usr/local/pgsql/data

# start the server
sudo -u postgres /usr/local/pgsql/bin/pg_ctl -D /usr/local/pgsql/data start

# stop the server
sudo -u postgres /usr/local/pgsql/bin/pg_ctl -D /usr/local/pgsql/data stop
```

##### Gdal - from source

Currently our API runs on a version of Debian that only has 2.4.\* versions of gdal available in stable.

Unfortunately brew can't install version 2.4.4. so it has to be manually installed.

required by: Postgis, gdal-python

```bash
wget https://download.osgeo.org/gdal/2.4.4/gdal-2.4.4.tar.gz
tar -xzf gdal-2.4.4.tar.gz
cd gdal-2.4.4
./configure
make
make install
```

##### Gettext - from source

required by: Postgis

```bash
wget https://ftp.gnu.org/pub/gnu/gettext/gettext-0.20.2.tar.gz
tar -xzf gettext-0.20.2.tar.gz
cd gettext-0.20.2
./configure
make
make install
```

##### Postgis - from source

Installing postgis with brew, will break gdal, so it too has to be installed from source.

requires: gettext

```bash
wget https://download.osgeo.org/postgis/source/postgis-3.0.1.tar.gz
tar -xzf postgis-3.0.1.tar.gz
cd postgis-3.0.1
./configure
make LDFLAGS="-L/usr/local/opt/gettext/lib" CPPFLAGS="-I/usr/local/opt/gettext/include"
sudo make install
```

##### Gdal - from brew

```bash
brew install gdal

```

##### Poetry

```bash
brew update
brew install pyenv
pyenv install 3.8.2
curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python
```

##### Install project python requirements

```bash
poetry env use 3.8
poetry install
poetry shell
# we can't include gdal in poetry as we have little control over the version of gdal available on different platforms - we must match whatever version of gdal is available on the system in question.
pip install gdal==$(gdal-config --version)
```

**N.B.: If `poetry env use 3.8` returns an `EnvCommandError` saying that "pyenv: python3.8: command not found", but `pyenv versions` shows that 3.8.x is installed, you must first run `pyenv shell 3.8.x` and then re-run `poetry env use 3.8`.**

##### Troubleshooting

###### psycopg2

If you experience errors when installing `psycopg2` and you are using MacOS, try running
`env LDFLAGS="-I/usr/local/opt/openssl@1.1/include -L/usr/local/opt/openssl@1.1/lib" poetry install`
from the command line.

If you're getting errors relating to `pg_config` executable not found when installing `psycopg2` it means
you either don't have PostgreSQL installed or psycopg2 doesn't know where to find it. You can install PostgreSQL by following instructions on <https://www.postgresql.org/download/>, be sure to update your PATH if you're installing it manually.

###### GDAL

If python gdal complains about header files, you may have to help it find them, export location before doing pip install

```bash
export CPLUS_INCLUDE_PATH=/usr/include/gdal
export C_INCLUDE_PATH=/usr/include/gdal
```

#### Local machine, running Linux

##### Ubuntu

Install system dependancies:

```bash
sudo apt install unixodbc-dev
sudo apt install python3-dev libpq-dev
sudo apt install libgdal-dev
```

##### Fedora

Install system dependancies:

```bash
sudo dnf install unixODBC-devel
```

#### R modules for cffdrs (MacOS Big Sur)

Make sure [GDAL is installed](#gdal-from-brew) on your system

```bash
- brew install r
- brew install udunits
- brew install proj
```

Within an R interpreter instance:

```R
- install.packages(c("rgdal","sf", "units"),,"https://mac.R-project.org")
- install.packages('cffdrs')
```

### Executing program

See [Makefile](Makefile) for examples of running the API in docker.

e.g.:

```bash
make init
```

will execute `poetry install`, which is required before executing the program locally for the first time.

```bash
make docker-run
```

will execute:

```bash
docker-compose up
```

#### Local machine, running mac os

See [Makefile](Makefile) for examples or running the API on your local machine.

e.g.:

```bash
make run
```

will execute:

```bash
poetry run pylint --rcfile=.pylintrc app/*.py app/**/*.py;
poetry run python -m pytest -n 3 app;
cd app; \
poetry run uvicorn main:app --reload --port 8080;
```

To shell into the Docker container for the database, execute `make docker-shell-db`.

### Running the database locally

Executing `make docker-build-dev` followed by `make docker-run-dev` will build and run the Docker container needed to run the application locally. Running the dev container will also spin up a local Postgres service and will create a local copy of the wps database with the necessary schemas.

To access the local copy of the database, you can shell into it by opening a new terminal window and executing `psql -h localhost -p 5432 -U <db-username>` and enter the local database password when prompted.

## Contributing

### Coding conventions

Code must be [PEP8](https://www.python.org/dev/peps/pep-0008/) compliant with the exception of allowing for line lengths up to 110 characters.
Compliance is enforced using [Pylint](https://www.pylint.org/) and a [.pylintrc](.pylintrc) file.

Run pylint to check that your code conforms before pushing code to the repository:

```bash
make lint
```

Or enforce by running [scripts/lint.sh](scripts/lint.sh) as part of your ci/cd pipeline.

### Testing

Code must pass all unit tests.

Run python unit tests before pushing code to the repository:

```bash
make test
```

Or enforce by running [scripts/test.sh](scripts/test.sh) as part of your ci/cd pipeline.

### Making changes to the database

After making a change to the model, create migration script:

```bash
PYTHONPATH=. alembic revision --autogenerate -m "Comment relevant to change"
```

You may have to modify the generated code to import geoalchemy2

Then apply:

```bash
PYTHONPATH=. alembic upgrade head
```

You may need to enable postgis extension:

```sql
CREATE EXTENSION postgis;

```

## Config Maps & Secrets

In `openshift/templates/global.config.yaml` there are templates for a global ConfigMap and global Secrets used by the API.
These templates can be applied to the Openshift project from the command line. For example, to apply the global.config template and pass a value for the WFWX-AUTH-URL parameter, run

`oc -n <openshift-project-name> process -f openshift/templates/global.config.yaml -p WFWX-AUTH-URL=https://spotwx.com/ | oc create -f -`

## Increasing Database Disk Space in Openshift

These are the steps necessary to increase the amount of disk space provisioned for the database hosted in **Openshift 3**:

### The easy way

1. Go to Storage -> Actions -> Expand PVC. Enter the desired size and click on expand.

2. That's it. No pod restarts required, the pods should pick up the increased size after a while.

### The hard way

1. From the Storage tab in the Openshift Cluster Console, delete the PVC of one of the Patroni replicas (note: a secondary replica, NOT the leader). Make a note of the PVC's name before you delete it.
2. From the Openshift Application Console, delete the pod associated with the PVC you just deleted. A new pod of the same name will immediately be recreated, but will not have any PVC to bind to yet. This is fine.
3. From the Openshift Cluster Console, create a new PVC.
   - the new PVC must have the same name as the PVC that was deleted in Step 1
   - set the requested storage to the desired size in Gi (GB)
   - delete all the labels that are set as defaults under the `selector` section in the YAML file. The PVC will fail to create and will be indefinitely stuck in the `Pending` state if there are any labels attached to the PVC
   - change the value of `storageClassName` from the default `slow` to `netapp-file-standard`. The `slow` storage class is not available in BCGov's incarnation of Openshift, so the PVC will be indefinitely stuck in the `Pending` state if the slow storage class is used.
   - click Create at the bottom of the screen
4. Once the newly created PVC has been initialized, the new pod from Step 2 will automatically bind to the new PVC. Resynchronization of the database on this pod will begin automatically.
5. Wait until the pod from Step 4 is Running and Ready (from the Application Console), then repeat the process with the other Patroni replica(s).
6. Perform steps 1-4 on the Patroni leader **last**.

## License

This project is licensed under the [Apache License, Version 2.0](https://github.com/bcgov/wps/blob/main/LICENSE).

## Acknowledgments

[![SonarCloud](https://sonarcloud.io/images/project_badges/sonarcloud-white.svg)](https://sonarcloud.io/dashboard?id=bcgov_wps)

Template copied from

- [DomPizzie](https://gist.github.com/DomPizzie/7a5ff55ffa9081f2de27c315f5018afc)
