#!/usr/bin/env bash

poetry config virtualenvs.in-project true --local
poetry env use 3.12.3
poetry run python -m pip install --upgrade pip
pip install sqlalchemy[asyncio]
poetry install
poetry run python -m pip install -e ../wps_shared
