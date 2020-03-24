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
	pipenv run pylint --rcfile=.pylintrc *.py **/*.py
	pipenv run python -m unittest
	pipenv run uvicorn main:APP --reload --port 8080

notebook:
	# Run jupyter notebooks.
	pipenv run jupyter notebook

shell:
	# Run shell in virtual environment shell.
	pipenv shell

docker-test:
	# Run tests in docker.
	docker-compose run dev scripts/test.sh

docker-lint:
	# Run lint in docker.
	docker-compose run dev scripts/lint.sh

docker-build:
	# Build docker images.
	docker-compose build

docker-run-dev:
	# Run docker in dev mode.
	# 1. run test and lint.
	docker-compose run dev scripts/test.sh
	docker-compose run dev scripts/lint.sh
	# 2. start api
	docker-compose run --service-ports api uvicorn main:APP --reload --host 0.0.0.0 --port 8080

docker-run:
	# Run api in production mode, in docker.
	docker-compose up
