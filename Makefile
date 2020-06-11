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
	# useful params for pytest:
	# -s show stdout
	poetry run pytest app;
	# ImportMismatchError? run: make clean

test-coverage:
	poetry run coverage run --source=app -m pytest;
	poetry run coverage report;
	poetry run coverage xml -o coverage-reports/coverage-report.xml;
	# ImportMismatchError? run: make clean

lint:
	# Run lint in virtual environment.
	poetry run pylint --rcfile=.pylintrc app/*.py app/**/*.py;

run:
	# Run the application in the virtual environment (after linting and testing).
	# Not failing on lint or test - just output so developer knows.
	-poetry run pylint --rcfile=.pylintrc app/*.py app/**/*.py;
	-poetry run python -m pytest app;
	cd app; \
		poetry run uvicorn main:app --reload --port 8080;

run-fast:
	cd app; \
		poetry run uvicorn main:app --reload --port 8080;

notebook:
	# Run jupyter notebooks.
	poetry run jupyter notebook

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
	docker-compose -f docker-compose.dev.yml run api-dev python -m pytest
	# ImportMismatchError? run: make clean

docker-run-dev:
	# Run docker in dev mode.
	docker-compose -f docker-compose.dev.yml up

docker-shell-dev:
	# Shell into the dev container.
	docker run -it --env-file app/.env --entrypoint bash wps-api_api-dev:latest 

docker-shell-dev-db:
	# Shell into the db container
	docker-compose exec db psql -h postgres -U wps

docker-build:
	# Build docker images.
	docker-compose build

docker-run:
	# Run api in production mode, in docker.
	docker-compose up
