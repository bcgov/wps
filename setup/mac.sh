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
# Grabs 3.12.3 formula -- https://github.com/Homebrew/homebrew-core/commits/master/Formula/g/gdal.rb
curl -s https://raw.githubusercontent.com/Homebrew/homebrew-core/2761c8e5f5547753c8bebc39e95968006f5deb69/Formula/g/gdal.rb > $(brew --repository)/Library/Taps/$(whoami)/homebrew-local-gdal/Formula/gdal.rb
brew install $(whoami)/local-gdal/gdal # if you have gdal/postgis already installed you'll have to uninstall them both, see MANUAL.md for more details

### For generated HFI Calculator PDFs
brew install --cask wkhtmltopdf

### pyenv
brew install pyenv
pyenv install 3.12.3
pyenv global 3.12.3

### uv
brew install uv

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
# echo "finished installing and configuration postgres, run migrations in poetry shell"

### redis
brew install redis
brew services start redis

echo "finished installing all local machine dependencies"