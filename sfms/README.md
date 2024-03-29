# SFMS script

## Overview

This project contains a script that is intended to be run on the SFMS windows server. The script is intended to be run after SFMS geotiffs have been generated and uploads all geotiffs to the PSU API.

The python script in this project, `sfms.py` is targeted at python 2.7, since the SFMS server is running python 2.7.

The python script, `sfms.py` does not require any external dependencies. [Python 2.7 is deprected](https://www.python.org/doc/sunset-python-2/) so we can't rely on pip being able to install any external dependencies.

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


### pyenv + 2.7.18 on M1

On M1, `pyenv install 2.7.18` fails, and will never pass (they're not going to bother fixing it, and they shouldn't! it's deprecated).

#### TODO: `pyenv install 2.7.18` and all subsequent commands above worked fine on my M1. Maybe it has been fixed after all?? Confirm with other devs

You CAN however try run a universal binary in x86_64 mode, and get it to work that way!

```bash
arch -x86_64 /bin/bash 
pyenv install -v 2.7.18
```

If the above option fails on your Mac M1, try this as well ([source](https://github.com/pyenv/pyenv/issues/2136)):

```bash
LDFLAGS="-L/opt/homebrew/Cellar/openssl@1.1/1.1.1m/lib" CPPFLAGS="-I/opt/homebrew/Cellar/openssl@1.1/1.1.1m/include" pyenv install 2.7.18
```
