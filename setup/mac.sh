#!/usr/bin/env bash

## Run this to install all project dependencies on a mac via brew

### homebrew
curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh

### openjdk
brew install openjdk

### Symlink it for mac
sudo ln -sfn /opt/homebrew/opt/openjdk/libexec/openjdk.jdk /Library/Java/JavaVirtualMachines/openjdk.jdk

### gh api
brew install gh

### gdal
brew tap-new $(whoami)/local-gdal
# Grabs 3.9.2 formula, needed until https://github.com/OSGeo/gdal/issues/13777 is fixed and we update the base image
curl -s https://raw.githubusercontent.com/Homebrew/homebrew-core/c230b76333dac4781414835c87811bdd09382ff4/Formula/g/gdal.rb > $(brew --repository)/Library/Taps/$(whoami)/homebrew-local-gdal/Formula/gdal.rb
brew install $(whoami)/local-gdal/gdal # if you have gdal/postgis already installed you'll have to uninstall them both, see MANUAL.md for more details

### For generated HFI Calculator PDFs
brew install --cask wkhtmltopdf

### pyenv
brew install pyenv
pyenv install 3.12.3
pyenv global 3.12.3

### uv
brew install uv

### r
brew install --cask r
brew install udunits
brew install proj

echo "installing r packages, this takes awhile..."
r -e 'install.packages(c("rgdal","sf", "units"),,"https://mac.R-project.org")'
r -e "install.packages('cffdrs', repos = 'http://cran.us.r-project.org')"
echo "finished installing r packages"

### postgres - Nov 2024 - Commenting out the postgres setup. See MANUAL.md for reasons and manual postgres setup.
# echo "installing and configuring postgres"
# brew install postgresql
# brew services start postgresql
# brew install postgis
# psql -d postgres -c "create database wps;"
# psql -d wps -c "create extension postgis;"
# psql -d wps -c "
# CREATE USER wps;
# CREATE USER wpsread;
# ALTER USER wps WITH LOGIN;
# ALTER USER wpsread WITH LOGIN;
# ALTER USER wps WITH SUPERUSER;
# grant connect on database wps to wpsread; grant usage on schema public to wpsread; grant select on all tables in schema public to wpsread;
# "
# echo "finished installing and configuration postgres, run migrations"

### redis
brew install redis
brew services start redis

echo "finished installing all local machine dependencies"