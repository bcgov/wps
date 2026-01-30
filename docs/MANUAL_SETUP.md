# Manual Setup

#### Local machine, in docker

For local development, you can copy .env.example to .env.docker.

```bash
docker compose build
```

#### Local machine, running MacOS

##### The simplest way to get started is to run the setup script:

```bash
./setup/mac.sh
```

##### To continue with manual setup, see below:

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

If you already have gdal installed above 3.9.2 you'll need to remove it and install a local version of the 3.9.2 version:

```bash
brew uninstall postgis #depends on gdal
brew uninstall gdal
brew untap gdal/versions
```

Then:

```bash
brew tap-new $(whoami)/local-gdal
curl -s https://raw.githubusercontent.com/Homebrew/homebrew-core/c230b76333dac4781414835c87811bdd09382ff4/Formula/g/gdal.rb > $(brew --repository)/Library/Taps/$(whoami)/homebrew-local-gdal/Formula/gdal.rb
brew install $(whoami)/local-gdal/gdal
```

Note that there are other subsequent steps for gdal installation. See "Install project python requirements".

##### wkhtmltopdf

```bash
brew install --cask wkhtmltopdf
```

##### uv

Try to match the latest version of python in our production environment (as of writing, API is on 3.12.3)

```bash
brew update
brew install pyenv
pyenv install 3.12.3
pyenv local 3.12.3
brew install uv
```

##### Install project python requirements

##### Troubleshooting

###### psycopg2

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
# isntall libudunits2-dev as required dependency of cffdrs
sudo apt install libudunits2-dev
# install R and pre-req for cffdrs
sudo apt install r-base
R
install.packages('rgdal')
install.packages('cffdrs')
# install the jdk (for running tests agains redapp)
sudo apt install default-jdk
```

##### Fedora

Install system dependencies:

```bash
sudo dnf install unixODBC-devel
```

#### R modules for cffdrs (MacOS)

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

See [Makefile](../Makefile) for examples of running the API in docker.

e.g.:

```bash
make init
```

```bash
make docker-run
```

will execute:

```bash
docker compose up
```

#### Local machine, running mac os

See [Makefile](../Makefile) for examples or running the API on your local machine.

e.g.:

```bash
make run
```

will execute:

```bash
uv run ruff .
cd app; \
uv run uvicorn main:app --reload --port 8080;
```

To shell into the Docker container for the database, execute `make docker-shell-db`.

### Running the database locally

#### In Docker

Executing `make docker-build-dev` followed by `make docker-run-dev` will build and run the Docker container needed to run the application locally. Running the dev container will also spin up a local Postgres service and will create a local copy of the wps database with the necessary schemas.

#### Natively

As of Nov 2024 the version of postgis installed with brew doesn't work with postgresql@16. postgis is specifically
linked to the original postgres cask (aka postgres@14). If you choose to use postgresql@16 installed via brew, you
will need to compile postgis yourself. The alternative is to use [Postgres.app](https://postgresapp.com/).

After installing Postgres.app, run the following commands in a terminal (taken from the mac.sh setup script):

```bash
psql -d postgres -c "create database wps;"
psql -d wps -c "create extension postgis;"
psql -d wps -c "
CREATE USER wps;
CREATE USER wpsread;
ALTER USER wps WITH LOGIN;
ALTER USER wpsread WITH LOGIN;
ALTER USER wps WITH SUPERUSER;
grant connect on database wps to wpsread; grant usage on schema public to wpsread; grant select on all tables in schema public to wpsread;
"
```

If you have chosen to `brew install postgresql@16` and compile `postgis` locally, follow the instructions below:

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

From `backend/packages/wps-api` run:

```bash
uv run alembic upgrade head
```

## New Workstation Setup

### Required Software

The following is a list of required software applications and packages. Some of these can be installed automatically using the `setup/mac.sh` script.

- VS Code (technically there are other options, but this is arguably the best)
- Git CLI
- GitHub CLI
- Openshift CLI
- Docker and Lima
- Brew (for Mac)

### Recommended VS Code Extensions

See [setup/vsc-extensions-install.sh](../setup/vsc-extensions-install.sh)
