#!/usr/bin/env bash

# run from wps root directory
echo $(pwd)

cd wps_shared
poetry run python -m pip install --upgrade pip
poetry install
poetry run python -m pip install gdal==$(gdal-config --version)

cd ../api
poetry run python -m pip install --upgrade pip
poetry install
poetry run python -m pip install gdal==$(gdal-config --version)
poetry run python -m pip install -e ../wps_shared

cd ../wps_jobs
poetry run python -m pip install --upgrade pip
poetry install
poetry run python -m pip install gdal==$(gdal-config --version)
poetry run python -m pip install -e ../wps_shared