# If the VIRTUAL_ENV is specified, we can assume we're in a poetry shell, otherwise
# we need to execute "poetry run"
ifdef VIRTUAL_ENV
POETRY_RUN=
else
POETRY_RUN=poetry run
endif

build:
	docker compose build

shell:
	docker compose run --rm backup bash

prune:
	docker compose run backup poetry run python prune.py

test:
	${POETRY_RUN} pytest

lint:
	${POETRY_RUN} pylint *.py