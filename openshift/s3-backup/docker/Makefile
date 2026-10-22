build:
	docker compose build

shell:
	docker compose run --rm backup bash

prune:
	docker compose run backup python3 prune.py

test:
	uv run pytest

lint:
	uv run ruff check *.py
