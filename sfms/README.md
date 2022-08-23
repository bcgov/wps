# SFMS script

## Overview

This project contains a script that is intended to be run on the SFMS windows
server. The script is intended to be run after SFMS geotiffs have been generated and uploads all geotiffs to the PSU API.

The python script in this project is targeted at python 2.7

## Run

```bash
python sfms.py config.ini
```

## Developer notes

Using poetry + pyenv you could configure your local development environment as follows:

```
pyenv install 2.7.18
pyenv shell 2.7.18
pyenv which python
poetry env use [use the output of the previous command]
poetry install
```