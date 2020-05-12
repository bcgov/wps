init:
	# Create virtual environment using pipenv.
	pipenv install --dev

test:
	# Run tests in virtual environment.
	pipenv run python -m unittest

lint:
	# Run lint in virtual environment.
	pipenv run pylint --rcfile=.pylintrc *.py **/*.py

run:
	# Run the application in the virtual environment (after linting and testing).
	# Not failing on lint or test - just output so developer knows.
	-pipenv run pylint --rcfile=.pylintrc *.py **/*.py
	-pipenv run python -m unittest
	pipenv run uvicorn main:APP --reload --port 8080

notebook:
	# Run jupyter notebooks.
	pipenv run jupyter notebook

shell:
	# Run shell in virtual environment shell.
	pipenv shell

docker-dev-test:
	# Run tests in docker (dev instance).
	# We use the dev instance, because the "production" version doesn't have
	# a number of the development dependancies.
	docker-compose -f docker-compose.dev.yml run api-dev pipenv run python -m unittest

docker-dev-lint:
	# Run lint in docker (dev instance).
	# We use the dev instance, because the "production" version doesn't have
	# a number of the development dependancies, including pylint.
	docker-compose -f docker-compose.dev.yml run api-dev pipenv run pylint --rcfile=.pylintrc *.py **/*.py

docker-build:
	# Build docker images.
	docker-compose build

docker-run:
	# Run api in production mode, in docker.
	docker-compose up

docker-build-dev:
	# Build dev docker images.
	docker-compose -f docker-compose.dev.yml build

docker-run-dev:
	# Run docker in dev mode.
	# 1. run test and lint.
	docker-compose -f docker-compose.dev.yml run api-dev pipenv run python -m unittest
	docker-compose -f docker-compose.dev.yml run api-dev pipenv run pylint --rcfile=.pylintrc *.py **/*.py
	# 2. start api
	docker-compose -f docker-compose.dev.yml up

docker-shell-dev:
	# Shell into the dev container.
	docker run -it --entrypoint bash wps-api_api-dev:latest 

