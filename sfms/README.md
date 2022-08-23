# SFMS script

## Overview

This project contains a script that is intended to be run on the SFMS windows server. The script is intended to be run after SFMS geotiffs have been generated and uploads all geotiffs to the PSU API.

The python script in this project, `sfms.py` is targeted at python 2.7, since the SFMS server is running python 2.7.

The pythong script, `sfms.py` does not require any external dependencies. [Python 2.7 is deprected](https://www.python.org/doc/sunset-python-2/) so we can't rely on pip being able to install any external dependencies.

## Run

The sfms.py script must be passed the location of a configuration file.

Example:

```bash
python sfms.py config.ini
```

## Configuration

The `config.ini` must be specifed, and has three fields that need to be configured:

- secret: This is a shared secret (password) between the SFMS server and the PSU API. If the secret does not match, then the PSU API will reject the request.
- source: this the directory where the geotiffs are located. All *.tif and *.tiff files in this directory will be uploaded.
- url: this is the url of the PSU API endpoint to which the script will post the geotiffs.

e.g.:

```config.ini
secret=secret
source=/home/user/sfms
destination=https://psu.nrs.gov.bc.ca/api/sfms/upload
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