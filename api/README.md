# Wildfire Predictive Services Unit API

## Description

Wildfire Predictive Services Unit support decision making in prevention, preparedness, response and recovery.

## Getting Started

### Dependencies

- Docker [Mac](https://hub.docker.com/editions/community/docker-ce-desktop-mac/), [Win](https://hub.docker.com/editions/community/docker-ce-desktop-windows/), [Ubuntu](https://docs.docker.com/install/linux/docker-ce/ubuntu/), [Fedora](https://docs.docker.com/install/linux/docker-ce/fedora/)

### Installing

You will need an environment file. See: .env.example.

#### Local machine, in docker

For local development, you can copy .env.example to .env.docker.

```bash
docker compose build
```

#### Local machine, running MacOS

For local development, you can copy .env.example to .env.

NOTE: matching the version of postgresql, postgis and gdal with production is problematic, and best
avoided. (postgresql + postgis binaries on mac use a newer version of gdal that we don't have on debian yet.)

NOTE: installing postgresql, postgis and gdal as binaries is the preffered method of installation. Installing
from source is a world of trouble you don't want to get into. Stick to brew.

##### Java

Some of the unit tests use jnius to compare output against RedAPP. The default version of Java that
comes with mac is likely to cause Segmentation Errors when you run unit tests.

Install the latest JDK! Download [https://jdk.java.net/](https://jdk.java.net/)

```bash
tar -xf openjdk-16.0.2_osx-x64_bin.tar.gz
sudo mv jdk-16.0.2.jdk /Library/Java/JavaVirtualMachines
```

Ensure that the CLASSPATH environment variable points to the jar files in api/libs, or unit tests will fail.

##### Gdal

```bash
brew install gdal
```

##### wkhtmltopdf

```bash
brew install --cask wkhtmltopdf
```

##### Poetry

Try to match the latest version of python in our production environment (as of writing, API is on 3.10.4)

```bash
brew update
brew install pyenv
pyenv install 3.10.4
pyenv local 3.10.4
curl -sSL https://install.python-poetry.org | python -
```

##### Install project python requirements

`poetry env use 3.10.4` doesn't actually honor the minor version, if you have more than one version
of 3.10, and you want 3.10.4 exactly, you have to find the location of the 3.10.4 binary and point
to that.

```bash
pyenv which python
```

```bash
poetry env use [path to python 3.10.4, get this by running 'pyenv which python']
poetry run python -m pip install --upgrade pip
poetry install
poetry shell
# we can't include gdal in poetry as we have little control over the version of gdal available on different platforms - we must match whatever version of gdal is available on the system in question.
python -m pip install gdal==$(gdal-config --version)
# on ubuntu, you may have to install pygdal, with the correct version specified.
python -m pip install pygdal==3.0.4.10
```

**N.B.: If `poetry env use [version]` returns an `EnvCommandError` saying something like "pyenv: python3.10: command not found", but `pyenv versions` shows that 3.10.4 is installed, you must first run `pyenv shell 3.10.4` and then re-run `poetry env use [path to python 3.10.4]`.**

##### Troubleshooting

###### psycopg2

If you experience errors when installing `psycopg2` and you are using MacOS, try running
`env LDFLAGS="-I/usr/local/opt/openssl@1.1/include -L/usr/local/opt/openssl@1.1/lib" poetry install`
from the command line.

If you're getting errors relating to `pg_config` executable not found when installing `psycopg2` it means
you either don't have PostgreSQL installed or psycopg2 doesn't know where to find it. You can install PostgreSQL by following instructions on <https://www.postgresql.org/download/>, be sure to update your PATH if you're installing it manually.

###### GDAL

If python gdal complains about header files (likely if you've installed gdal manually), you may have to help it find them, export location before doing pip install:

```bash
export CPLUS_INCLUDE_PATH=/usr/include/gdal
export C_INCLUDE_PATH=/usr/include/gdal
```

If gdal isn't installing, and you're on a mac, getting errors like "/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX.sdk/usr/include/c++/v1/cmath:321:9: error: no member named 'signbit' in the global namespace using ::signbit;" then try the following:

- ensure you've applied most recent OS updates.
- ensure XCode is updated.
- wipe your existing virtual environment

#### Local machine, running Linux

##### Ubuntu

Install system dependancies:

```bash
sudo apt install python3 python3-pip
sudo apt install python-is-python3
# install osgeo/gdal
sudo apt install libgdal-dev
# install R and pre-req for cffdrs
sudo apt install r-base
R
install.packages('rgdal')
install.packages('cffdrs')
# install the jdk (for running tests agains redapp)
sudo apt install default-jdk
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
docker compose up
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

#### In Docker

Executing `make docker-build-dev` followed by `make docker-run-dev` will build and run the Docker container needed to run the application locally. Running the dev container will also spin up a local Postgres service and will create a local copy of the wps database with the necessary schemas.

#### Natively

If you're running Postgresql natively for the first time:

```bash
brew services start postgresql
brew services list
```

should show that the "postgresql" service is running.

```bash
psql -d postgres
```

will shell you into your local postgres server.

```psql
create user wps with password "wps";
```

(or your desired username/password combo. Make sure to update these in your .env file).
If successful, this command will output `CREATE ROLE`.

```psql
create database wps with owner wps;
```

If successful, this command will output `CREATE DATABASE`.

`\l` should show "wps" in the list of databases.

```psql
\c wps
\dx
```

will show the list of extensions, and "postgis" should be one of them. If it isn't, run

```psql
create extension postgis;
```

If successful, this command will output `CREATE EXTENSION`. Re-run `\dx` to confirm the postgis extension has now been added.

From a poetry shell, run

```bash
PYTHONPATH=. alembic upgrade head
```

---

To access the local copy of the database, you can shell into it by opening a new terminal window and executing `psql -h localhost -p 5432 -U <db-username>` and enter the local database password when prompted.

## Maintenance

### Reverting Deployment

To redeploy prod from a previous image:

1. Find the previous working image in openshift and run
   - `oc -n e1e498-tools tag wps-prod:pr-<last-working-pr-number> wps-prod:prod`
2. Select "Start rollout" action in openshift

### Disk space

A subset of model predictions is currently being stored, but not actually used once interpolation has been
performed. This data can be trimmed in order to preserve space:

```sql
delete from model_run_grid_subset_predictions where prediction_timestamp < now() - interval '3 months'
```

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

Or run continuously with pytest-testmon and pytest-watch (`ptw --runner "pytest --testmon"` or `ptw -- --testmon`):

```bash
make test-watch
```

Or enforce by running [scripts/test.sh](scripts/test.sh) as part of your ci/cd pipeline.


#### ModuleNotFoundError: No module named 'pkg_resources'

```bash
poetry run python -m pip install --upgrade setuptools
```

### Making changes to the database

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
