#!/usr/bin/env bash

PYTHON_VERSION=3.12.3

# create virtual environments inside the project dirs
poetry config virtualenvs.in-project true

# run from wps root directory
echo $(pwd)

cd wps_shared
poetry env use "$PYTHON_VERSION"
poetry run python -m pip install --upgrade pip
poetry install
poetry run python -m pip install gdal==$(gdal-config --version)

cd ../api
poetry env use "$PYTHON_VERSION"
poetry run python -m pip install --upgrade pip
poetry install
poetry run python -m pip install gdal==$(gdal-config --version)
poetry run python -m pip install -e ../wps_shared

cd ../wps_jobs
poetry env use "$PYTHON_VERSION"
poetry run python -m pip install --upgrade pip
poetry install
poetry run python -m pip install gdal==$(gdal-config --version)
poetry run python -m pip install -e ../wps_shared