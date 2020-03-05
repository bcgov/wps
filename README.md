# Wildfire Predictive Services FWI Percentile Calculator API

## Description

Wildfire Predictive Services support decision making in prevention, preparedness, response and recovery.

## Getting Started

### Dependencies

* Docker [Mac](https://hub.docker.com/editions/community/docker-ce-desktop-mac/), [Win](https://hub.docker.com/editions/community/docker-ce-desktop-windows/), [Ubuntu](https://docs.docker.com/install/linux/docker-ce/ubuntu/), [Fedora](https://docs.docker.com/install/linux/docker-ce/fedora/)

* Docker Compose

```
brew install docker-compose
```

### Installing

You will need a .env file, see sample.env. For local development, you can copy sample.env to .env

```
cd code
docker-compose build
```

#### On your local MacOS

Do so at your own risk!

Install system dependancies:
```
brew install pyenv
pyenv install 3.6.10
brew install pipenv
```

Install project requirements:
```
cd wps-api
pipenv install --dev
```
If you have trouble getting pipenv to resolve python 3.8.1, you can also try:
```
pipenv install --python ~/.pyenv/versions/3.6.10/bin/python3.6 --dev
```
#### Local machine, running Ubuntu os 

If you have trouble installing pyodbc, you can try:
```
sudo apt install unixodbc-dev
```

### Executing program

Running the web service in docker:
```
docker-compose up
```
Running unit tests in docker:
```
docker-compose run web python -m unittest
```

#### Local machine, running mac os

Run it:
```
pipenv run uvicorn main:app --reload
```
or
```
make run
```

Run tests:
```
pipenv run python -m unittest
```
or
```
make test
```

Running jupyter notebooks:
```
pipenv run jupyter notebook
```
or
```
make notebook
```

Shell:
```
pipenv shell
```

## Architecture

![FWI calculator container diagram](container_diagram.png)

## License

This project is licensed under the [Apache License, Version 2.0](https://github.com/bcgov/wps-api/blob/master/LICENSE).

## Acknowledgments

Template copied from
* [DomPizzie](https://gist.github.com/DomPizzie/7a5ff55ffa9081f2de27c315f5018afc)
