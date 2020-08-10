define run-test
	# function to run tests
	# useful params for pytest:
	# -s show stdout
	$(1) pytest -n 4 app;
	# ImportMismatchError? run: make clean
endef

define run-test-coverage
	# function to run tests with coverate reports
	$(1) coverage run --source=app -m pytest;
	$(1) coverage report;
	$(1) coverage xml -o coverage-reports/coverage-report.xml;
	# ImportMismatchError? run: make clean
endef

define run-lint
	# function to run linting
	${1} pylint -j 0 --rcfile=.pylintrc app/*.py app/**/*.py;
endef

define run-api
	# function to run api
	${1} uvicorn app.main:app --host 0.0.0.0 --reload --port 8080;
endef

clean:
	find . -name \*.pyc -delete

init:
	# Create virtual environment.
	poetry install;

init-mac:
	# Create virtual environment.
	env LDFLAGS="-I/usr/local/opt/openssl@1.1/include -L/usr/local/opt/openssl@1.1/lib" poetry install

test:
	# Run tests in virtual environment.
	${call run-test,poetry run}

test-raw:
	# Assumes you've run 'poetry shell', or have installed all dependancies.
	${call run-test}

test-coverage:
	${call run-test-coverage,poetry run}	

test-coverage-raw:
	# Assumes you've run 'poetry shell', or have installed all dependancies.
	${call run-test-coverage}	

lint:
	# Run lint in virtual environment.
	${call run-lint,poetry run}

lint-raw:
	${call run-lint}

run:
	# Run the application in the virtual environment (after linting and testing).
	# Not failing on lint or test - just output so developer knows.
	-poetry run pylint --rcfile=.pylintrc app/*.py app/**/*.py;
	-poetry run python -m pytest app;
	${call run-api,poetry run}

run-fast:
	${call run-api,poetry run}

run-raw:
	# Assumes you've run 'poetry shell', or have installed all dependancies.
	${call run-api}

run-env-canada-raw:
	POSTGRES_HOST=localhost python -m app.models.env_canada

notebook:
	# Run jupyter notebooks.
	POSTGRES_HOST=localhost PYTHONPATH=$(shell pwd) JUPYTER_PATH=$(shell pwd) poetry run jupyter notebook --ip 0.0.0.0

shell:
	# Run shell in virtual environment shell.
	poetry shell

docker-build-dev:
	# Build dev docker images.
	# Having issues? try: docker volume prune
	# Still having issues? try: docker system prune
	docker-compose -f docker-compose.dev.yml build

docker-test-dev:
	# Run tests in docker (dev instance).
	# We use the dev instance, because the "production" version doesn't have
	# a number of the development dependancies.
	docker-compose -f docker-compose.dev.yml run api-dev python -m pytest app
	# ImportMismatchError? run: make clean

docker-run-dev:
	# Run docker in dev mode.
	docker-compose -f docker-compose.dev.yml up

docker-shell-dev:
	# Shell into the dev container.
	# docker run -it --env-file app/.env --entrypoint bash wps-api_api-dev:latest
	docker-compose run api bash

docker-shell-dev-db:
	# Shell into the db container
	docker-compose exec db psql -h db -U wps

docker-build:
	# Build docker images.
	docker-compose build

docker-run:
	# Run api in production mode, in docker.
	docker-compose up
