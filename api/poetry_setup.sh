#!/usr/bin/env bash

poetry config virtualenvs.in-project false --local
poetry env use 3.10.4
poetry run python -m pip install --upgrade pip
pip install sqlalchemy[asyncio]
poetry install
python -m pip install gdal==$(gdal-config --version)
