#!/usr/bin/env bash

## Run this to install all project dependencies on a mac via brew.
## Safe to re-run: every step is idempotent.

set -euo pipefail

### homebrew
if ! command -v brew >/dev/null 2>&1; then
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi
# Ensure brew is on PATH for the rest of this script (it isn't, in the shell that
# just bootstrapped it on a fresh machine).
if [[ -x /opt/homebrew/bin/brew ]]; then
  eval "$(/opt/homebrew/bin/brew shellenv)"
elif [[ -x /usr/local/bin/brew ]]; then
  eval "$(/usr/local/bin/brew shellenv)"
fi
# Full path to brew (works on Apple Silicon /opt/homebrew and Intel /usr/local); used
# in the shell-config instructions printed at the end.
BREW_EXE="$(command -v brew)"

### openjdk (for jnius/RedAPP unit tests)
brew install openjdk
# Point JAVA_HOME at the brew openjdk (no sudo symlink needed). pyjnius/RedAPP tests
# read this. Exported for this script run only; the instructions printed at the end
# tell the user how to persist it in their preferred shell.
JAVA_HOME_VAL="$(brew --prefix openjdk)/libexec/openjdk.jdk/Contents/Home"
export JAVA_HOME="$JAVA_HOME_VAL"

### gh api
brew install gh

### gdal
# The python gdal binding (pinned in backend/packages/*/pyproject.toml) builds from source
# against the installed libgdal, which must be >= the pinned version. The pin tracks the
# ghcr.io/osgeo/gdal base image tag (see openshift/wps-api-base/docker/Dockerfile); keep
# the base image tag and the pyproject pins in step when bumping.
#
# We intentionally do NOT `brew pin gdal`. Pinning the formula doesn't pin its
# dependencies, so a later `brew upgrade` of poppler/proj/etc. can move a dylib soname and
# break gdal anyway. Instead we let homebrew keep gdal consistent with its deps; if gdal
# drifts ahead of the pinned version the `uv sync` / gdal build fails loudly, which is the
# signal to bump the pyproject pins + base image (and re-run `uv sync`).
brew install gdal

### ecCodes (for weather model unit tests)
brew install eccodes

### wkhtmltopdf (for generating HFI Calculator PDFs)
# wkhtmltopdf is discontinued and the Homebrew cask is gone. The only macOS package is
# the older 0.12.6-2 x86_64 ("cocoa") build, so on Apple Silicon it needs Rosetta 2.
# Installing the .pkg requires sudo. This is optional -- only HFI PDF generation needs
# it -- so failures here are non-fatal and won't abort the rest of setup.
WKHTMLTOPDF_PKG_URL="https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-2/wkhtmltox-0.12.6-2.macos-cocoa.pkg"
if command -v wkhtmltopdf >/dev/null 2>&1; then
  echo "wkhtmltopdf already installed; skipping."
else
  (
    set -e
    # The macOS build is x86_64 -- install Rosetta 2 so it runs on Apple Silicon.
    if [[ "$(uname -m)" == "arm64" ]]; then
      sudo softwareupdate --install-rosetta --agree-to-license
    fi
    curl -L -o /tmp/wkhtmltox.pkg "$WKHTMLTOPDF_PKG_URL"
    sudo installer -pkg /tmp/wkhtmltox.pkg -target /
    rm -f /tmp/wkhtmltox.pkg
  ) || echo "WARNING: wkhtmltopdf install failed (optional; only needed for HFI PDF generation). Continuing."
fi

### pyenv + python
brew install pyenv
pyenv install -s 3.12.3
pyenv global 3.12.3

### uv
brew install uv

### postgres + postgis
# Homebrew's postgis depends on the current homebrew-core gdal, which now matches the
# project's pinned gdal (see the gdal note above), so brew postgis no longer collides
# with it -- the Nov 2024 reason for avoiding brew postgres is resolved.
# postgis ships bottles for postgresql@17 and @18; we use @17.
echo "installing and configuring postgres"
brew install postgresql@17 postgis
brew services start postgresql@17
# postgresql@17 is keg-only; expose its client tools (psql, pg_config) on PATH.
# pg_config is required for the psycopg2 source build during `uv sync`. Exported for
# this script run only; the instructions printed at the end tell the user how to
# persist it in their preferred shell.
PG_BIN="$(brew --prefix postgresql@17)/bin"
export PATH="$PG_BIN:$PATH"
# wait for the server to accept connections before creating the database
for _ in $(seq 1 15); do
  if pg_isready -q; then break; fi
  sleep 1
done
# create the wps database, extension and users (each step idempotent)
psql -d postgres -tc "SELECT 1 FROM pg_database WHERE datname='wps'" | grep -q 1 \
  || psql -d postgres -c "create database wps;"
psql -d wps -c "CREATE EXTENSION IF NOT EXISTS postgis;"
psql -d wps -tc "SELECT 1 FROM pg_roles WHERE rolname='wps'" | grep -q 1 \
  || psql -d wps -c "CREATE USER wps;"
psql -d wps -tc "SELECT 1 FROM pg_roles WHERE rolname='wpsread'" | grep -q 1 \
  || psql -d wps -c "CREATE USER wpsread;"
psql -d wps -c "
ALTER USER wps WITH LOGIN;
ALTER USER wpsread WITH LOGIN;
ALTER USER wps WITH SUPERUSER;
ALTER USER wps WITH PASSWORD 'wps';
grant connect on database wps to wpsread; grant usage on schema public to wpsread; grant select on all tables in schema public to wpsread;
"
echo "finished installing and configuring postgres; run migrations with: (cd backend/packages/wps-api && uv run --package wps-api alembic upgrade head)"

### redis
brew install redis
brew services start redis

echo "finished installing all local machine dependencies"

### Shell configuration
# The variables above were exported for this script run only. Print instructions so
# the user can persist them in whatever shell they use (we don't edit profiles for them).
cat <<EOF

============================================================
ADD THESE TO YOUR SHELL PROFILE
============================================================
These were set for this script run only. Add the lines for
your shell so new terminals have:
  - brew on PATH
  - JAVA_HOME (for pyjnius/RedAPP tests)
  - postgresql@17 client tools (psql, pg_config -- 'uv sync')

bash / zsh  (e.g. ~/.zprofile, ~/.bash_profile, ~/.zshrc):

  eval "\$($BREW_EXE shellenv)"
  export JAVA_HOME="$JAVA_HOME_VAL"
  export PATH="$PG_BIN:\$PATH"

fish  (~/.config/fish/config.fish):

  $BREW_EXE shellenv fish | source
  set -gx JAVA_HOME "$JAVA_HOME_VAL"
  fish_add_path "$PG_BIN"
============================================================
EOF
