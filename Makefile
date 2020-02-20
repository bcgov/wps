init:
	pipenv install --dev

test:
	pipenv run python -m unittest

docker-test:
	docker-compose run web python -m unittest

run:
	pipenv run uvicorn main:app --reload --port 8080

notebook:
	pipenv run jupyter notebook

shell:
	pipenv shell