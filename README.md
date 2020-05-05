# Wildfire Predictive Services FWI Percentile Calculator API

## Description

Wildfire Predictive Services support decision making in prevention, preparedness, response and recovery.

## Getting Started

### Dependencies

- Docker [Mac](https://hub.docker.com/editions/community/docker-ce-desktop-mac/), [Win](https://hub.docker.com/editions/community/docker-ce-desktop-windows/), [Ubuntu](https://docs.docker.com/install/linux/docker-ce/ubuntu/), [Fedora](https://docs.docker.com/install/linux/docker-ce/fedora/)

- Docker Compose

```
brew install docker-compose
```

### Installing

You will need a .env file, .env.example ; For local development, you can copy .env.example to .env.

#### Local machine, in docker

```
docker-compose build
```

#### Local machine, running MacOS

Install system dependancies:

```
brew install pyenv
pyenv install 3.8.1
brew install pipenv
```

Install project requirements:

```
cd wps-api
pipenv install --dev
```

If you have trouble getting pipenv to resolve python 3.8.1, you can also try explicitly specifying the python location:

```
pipenv install --python ~/.pyenv/versions/3.8.1/bin/python3.8 --dev
```

#### Local machine, running Linux

If you have trouble installing pyodbc, you can try:

##### Ubuntu

```
sudo apt install unixodbc-dev
```

##### Fedora

```
sudo dnf install unixODBC-devel
```

### Executing program

See [Makefile](Makefile) for examples of running the API in docker.

e.g.:

```
make docker-run
```

will execute:

```
docker-compose run api scripts/test.sh
docker-compose up
```

#### Local machine, running mac os

See [Makefile](Makefile) for examples or running the API on your local machine.

e.g.:

```
make run
```

will execute:

```
pipenv run pylint --rcfile=.pylintrc *.py **/*.py
pipenv run python -m unittest
pipenv run uvicorn main:APP --reload --port 8080
```

## Contributing

### Coding conventions

Code must be [PEP8](https://www.python.org/dev/peps/pep-0008/) compliant with the exception of allowing for line lengths up to 110 characters.
Compliance is enforced using [Pylint](https://www.pylint.org/) and a [.pylintrc](.pylintrc) file.

Run pylint to check that your code conforms before pushing code to the repository:

```
make lint
```

Or enfore by running [scripts/lint.sh](scripts/lint.sh) as part of your ci/cd pipeline.

### Testing

Code must pass all unit tests.

Run python unit tests before pushing code to the repository:

```
make test
```

Or enforce by running [scripts/test.sh](scripts/test.sh) as part of your ci/cd pipeline.

## Architecture

![FWI calculator container diagram](container_diagram.png)

## License

This project is licensed under the [Apache License, Version 2.0](https://github.com/bcgov/wps-api/blob/master/LICENSE).

## Acknowledgments

Template copied from

- [DomPizzie](https://gist.github.com/DomPizzie/7a5ff55ffa9081f2de27c315f5018afc)
