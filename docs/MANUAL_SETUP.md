# Manual Setup

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

##### Artifactory npm repo config

We currently publish the cffdrs_ts package to our internal artifactory instance. You need to configure credentials so npm can pull the cffdrs_ts package from this repo. To add the credentials to your global `~/.npmrc` run:

```bash
npm config set @psu:registry https://artifacts.developer.gov.bc.ca/artifactory/api/npm/pe1e-psu-npm-local/
npm config set //artifacts.developer.gov.bc.ca/artifactory/api/npm/pe1e-psu-npm-local/:_authToken {artifactory_token}
```

Alternatively, you can create a project specific `.npmrc` at the root of the `web` directory and add the following:
`@psu:registry=https://artifacts.developer.gov.bc.ca/artifactory/api/npm/pe1e-psu-npm-local/`
`//artifacts.developer.gov.bc.ca/artifactory/api/npm/pe1e-psu-npm-local/:_authToken={artifactory_token}`

The artifactory token is currently stored in Vault as gha_artifactory_token.

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

##### Poetry

Try to match the latest version of python in our production environment (as of writing, API is on 3.12.3)

```bash
brew update
brew install pyenv
pyenv install 3.12.3
pyenv local 3.12.3
curl -sSL https://install.python-poetry.org | python -
```

##### Install project python requirements

`poetry env use 3.12.3` doesn't actually honor the minor version, if you have more than one version
of 3.10, and you want 3.12.3 exactly, you have to find the location of the 3.12.3 binary and point
to that.

```bash
pyenv which python
```

```bash
poetry env use [path to python 3.12.3, get this by running 'pyenv which python']
poetry run python -m pip install --upgrade pip
```

Add the artifactory repo source to your poetry config:

```bash
poetry source add --priority=supplemental psu https://artifacts.developer.gov.bc.ca/artifactory/api/pypi/{repo_name}/simple
```

Add artifactory repo credentials to poetry config:

```bash
poetry config http-basic.psu <service-account-username> <service-account-password>
```

Install dependencies:

In each individual workspace you must do the following

```bash
poetry install
# we can't include gdal in poetry as we have little control over the version of gdal available on different platforms - we must match whatever version of gdal is available on the system in question.
poetry run python -m pip install gdal==$(gdal-config --version)

# Install the wps_shared package in editable mode using pip to allow changes in the wps_shared package to be reflected immediately in the api package. This is not needed in the wps_shared workspace.
poetry run python -m pip install -e ../wps_shared

# on ubuntu, you may have to install pygdal, with the correct version specified.
poetry run python -m pip install pygdal==3.0.4.10
```

**N.B.: If `poetry env use [version]` returns an `EnvCommandError` saying something like "pyenv: python3.10: command not found", but `pyenv versions` shows that 3.12.3 is installed, you must first run `pyenv shell 3.12.3` and then re-run `poetry env use [path to python 3.12.3]`.**

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
poetry run ruff .
cd app; \
poetry run uvicorn main:app --reload --port 8080;
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

From a poetry shell, run

```bash
PYTHONPATH=. alembic upgrade head
```

Or enforce by running [scripts/test.sh](scripts/test.sh) as part of your ci/cd pipeline.

#### ModuleNotFoundError: No module named 'pkg_resources'

```bash
poetry run python -m pip install --upgrade setuptools
```

## New Workstation Setup

### Required Software

The following is a list of required software applications and packages. Some of these can be installed automatically using the `setup/mac.sh` script.

- VS Code (technically there are other options, but this is arguably the best)
  - using the "Python: select interpreter" command within VS Code, select the `pyenv` Python installation
- Git CLI
- GitHub CLI
- Openshift CLI
- Docker and Lima
- Brew (for Mac)

### Optional but Recommended Software

- [Fig (for Mac)](https://fig.io/)
- [Oh My Zsh](https://ohmyz.sh/)
- [Zenhub extension for GitHub](https://www.zenhub.com/extension)

### Recommended VS Code Extensions

The extensions listed here are shown exactly as they appear in the VS Code Extensions marketplace.

- Copy without formatting
- Dev Containers
- Docker
- ESLint
- Fig (not available through the Extensions Marketplace within VS Code, but when Fig is installed via CLI, the Fig extension will automatically be available in VS Code)
- GitLens - Git supercharged
- Isort
- Jupyter
- Jupyter Cell Tags
- Jupyter Keymap
- Jupyter Notebook Renderers
- Jupyter Slide Show
- Makefile Tools
- Markdown All in One
- markdownlint
- Markdown Preview Enhanced
- Markdown+Math
- Math to Image
- Prettier - Code formatter
- Pylance
- Python
- R
- Rainbow Brackets
- Remote - SSH
- SonarLint
- VS Code Counter
