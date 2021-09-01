
docker-build:
	# Build dev docker images.
	# Having issues? try: docker volume prune
	# Still having issues? try: docker system prune
	docker-compose build

docker-run:
	# Run docker in dev mode.
	docker-compose up

docker-db:
	# Run the database
	docker-compose up db

docker-shell-web:
	# Shell into the dev container.
	# docker run -it --env-file app/.env --entrypoint bash wps-api_api:latest
	docker-compose run --rm web bash