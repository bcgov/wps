#!/usr/bin/env bash

## Run this to install all project dependencies on a mac

### homebrew
curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh

### openjdk
brew install openjdk

### Symlink it for mac
sudo ln -sfn /opt/homebrew/opt/openjdk/libexec/openjdk.jdk /Library/Java/JavaVirtualMachines/openjdk.jdk

### gdal
brew install gdal

### For generated HFI Calculator PDFs
brew install --cask wkhtmltopdf

### pyenv
brew install pyenv
pyenv install 3.10.4
pyenv global 3.10.4

### poetry
curl -sSL https://install.python-poetry.org | python -
echo "poetry installed, run poetry_setup.sh in api"

### r
brew install --cask r
brew install udunits
brew install proj

echo "installing r packages, this takes awhile..."
r -e 'install.packages(c("rgdal","sf", "units"),,"https://mac.R-project.org")'
r -e "install.packages('cffdrs', repos = 'http://cran.us.r-project.org')"
echo "finished installing r packages"

### postgres
echo "installing and configuring postgres"
brew install postgresql
brew services start postgresql
brew install postgis
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
echo "finished installing and configuration postgres, run migrations in poetry shell"