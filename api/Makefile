# If the VIRTUAL_ENV is specified, we can assume we're in a poetry shell, otherwise
# we need to execute "poetry run"
ifdef VIRTUAL_ENV
POETRY_RUN=
else
POETRY_RUN=poetry run
endif

define run-api
	# function to run api
	${1} uvicorn app.main:app --host 0.0.0.0 --reload --port 8080;
endef

define build-static
	# function to build static content
	cd ../web; REACT_APP_KEYCLOAK_AUTH_URL="{{REACT_APP_KEYCLOAK_AUTH_URL}}" REACT_APP_MATOMO_URL="{{REACT_APP_MATOMO_URL}}" REACT_APP_MATOMO_SITE_ID="{{REACT_APP_MATOMO_SITE_ID}}" REACT_APP_MATOMO_CONTAINER="{{REACT_APP_MATOMO_CONTAINER}}" npm run build
endef

define run-env-canada-model
	POSTGRES_HOST=localhost $(POETRY_RUN) python -m app.weather_models.env_canada ${1}
endef

define run-env-canada
	${call run-env-canada-model,GDPS}
	${call run-env-canada-model,HRDPS}
	${call run-env-canada-model,RDPS}
endef

clean:
	# delete python bytecode.
	find . -name \*.pyc -delete
	# clean out the static folder - leaving the placeholder alone.
	find static ! -name 'placeholder.txt' ! -name 'static' -exec rm -rf {} +

init:
	# Create virtual environment.
	poetry install;
	# Create static content
	${call build-static}

init-mac:
	# Create virtual environment.
	env LDFLAGS="-I/usr/local/opt/openssl@1.1/include -L/usr/local/opt/openssl@1.1/lib" poetry install
	# Create static content
	${call build-static}

test:
	# Run tests
	# useful params for pytest:
	# -s show stdout
	# -n numprocesses - doesn't really seem to run faster with more proccesses at the moment.
	PYTHONPYCACHEPREFIX=python_cache $(POETRY_RUN) pytest -n 3 app;
	# ImportMismatchError? run: make clean

test-verbose:
	# Run tests with verbose output
	$(POETRY_RUN) pytest app -n 2 -vv;

test-coverage:
	# run tests with coverate reports
	$(POETRY_RUN) coverage run --source=app -m pytest;
	$(POETRY_RUN) coverage report;
	$(POETRY_RUN) coverage xml -o coverage-reports/coverage-report.xml;
	# ImportMismatchError? run: make clean

lint:
	# Run lint.
	$(POETRY_RUN) pylint --rcfile=.pylintrc app/*.py app/**/*.py;

run:
	# Run the application in the virtual environment (after linting and testing).
	# Not failing on lint or test - just output so developer knows.
	-poetry run pylint --rcfile=.pylintrc app/*.py app/**/*.py;
	-poetry run python -m pytest -n 3 app;
	${call run-api,$(POETRY_RUN)}

run-fast:
	${call run-api,$(POETRY_RUN)}

run-env-canada:
	${call run-env-canada}

run-env-canada-gdps:
	${call run-env-canada-model,GDPS}

run-env-canada-hrdps:
	${call run-env-canada-model,HRDPS}

run-env-canada-rdps:
	${call run-env-canada-model,RDPS}

run-donald:
	# Synonymn for run-env-canada-raw
	${call run-env-canada}

run-bender:
	$(POETRY_RUN) python -m app.fireweather_bot.noon_forecasts

run-noon-forecasts:
	$(POETRY_RUN) python -m app.fireweather_bot.noon_forecasts

run-marvin:
	$(POETRY_RUN) python -m app.fireweather_bot.hourly_actuals

run-hourly-observed:
	$(POETRY_RUN) python -m app.fireweather_bot.hourly_actuals

run-all-bots:
	${call run-env-canada}
	$(POETRY_RUN) python -m app.fireweather_bot.hourly_actuals
	$(POETRY_RUN) python -m app.fireweather_bot.noon_forecasts


c-haines:
	$(POETRY_RUN) python -m app.c_haines.worker


fetch-database-partial:
	$(POETRY_RUN) python scripts/copy_db_from_pod_to_local.py

fetch-database-complete:
	$(POETRY_RUN) python scripts/copy_db_from_pod_to_local.py --mode=complete

restore-partial-database-local:
	# Restore a partial database to local server.
	# Set environment variable PGPASSWORD=mywpspassword if you want to skip typing password for authentication.
	# Set environment variable WITH_WPSREAD if you want to grant rights for wpsread user.
	MODE=native ./scripts/restore_db.sh

restore-complete-database-local:
	# Restore a complete database to local server.
	MODE=native PARTIAL=False ./scripts/restore_db.sh

restore-partial-database-docker:
	# Restore a partial database to server in docker.
	# Set environment variable PGPASSWORD=mywpspassword if you want to skip typing password for authentication.
	# Set environment variable WITH_WPSREAD if you want to grant rights for wpsread user.
	./scripts/restore_db.sh

notebook:
	# Run jupyter notebooks.
	POSTGRES_HOST=localhost PYTHONPATH=$(shell pwd) JUPYTER_PATH=$(shell pwd) poetry run jupyter notebook --ip 0.0.0.0

shell:
	# Run shell in virtual environment shell.
	poetry shell

docker-build:
	# Build dev docker images.
	# Having issues? try: docker volume prune
	# Still having issues? try: docker system prune
	docker-compose build

docker-lint:
	# Run linting in docker (dev instance).
	${call run-lint,docker-compose run --rm api}

docker-test:
	# Run tests in docker (dev instance).
	# We use the dev instance, because the "production" version doesn't have
	# a number of the development dependancies.
	# Make sure that your docker pycache doesn't conflict with your local pycache.
	docker-compose run --rm api pytest -n 3 app

docker-test-coverage:
	# Run tests with coverage in docker (dev instance).
	${call run-test-coverage,docker-compose run --rm api}
	
docker-shell:
	# Shell into the dev container.
	# docker run -it --env-file app/.env --entrypoint bash wps-api_api:latest
	docker-compose run --rm api bash

docker-run:
	# Run docker in dev mode.
	docker-compose up

docker-shell-db:
	# Shell into the db container
	docker-compose exec db psql -h db -U wps

docker-run-env-canada:
	# Run a python script to download model data from Env Canada on docker
	# Needs to run "make docker-run" first
	docker-compose exec api python -m app.weather_models.env_canada GDPS
	docker-compose exec api python -m app.weather_models.env_canada HRDPS
	docker-compose exec api python -m app.weather_models.env_canada RDPS

docker-run-donald:
	# Synonymn for docker-run-env-canada
	docker-compose exec api python -m app.weather_models.env_canada GDPS
	docker-compose exec api python -m app.weather_models.env_canada HRDPS
	docker-compose exec api python -m app.weather_models.env_canada RDPS

docker-run-bender:
	# Run a python script to download forecast data from BC Wild Fire on docker
	# Needs to run "make docker-run" first
	docker-compose exec api python -m app.fireweather_bot.noon_forecasts

docker-run-marvin:
	# Run a python script to download hourly actuals from BC Wild Fire on docker.
	# Needs to run "make docker-run" first
	docker-compose exec api python -m app.fireweather_bot.hourly_actuals
