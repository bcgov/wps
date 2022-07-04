
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

docker-web-server-build:
	# Build the web in server mode (same dockerfile as used in production)
	docker build -f ./Dockerfile.web --tag=wps/web .

docker-web-server:
	# Run the web in server mode (same dockerfile as used in production)
	docker run -p 3000:3000 wps/web

docker-shell-api:
	# Shell into the dev container.
	docker-compose run --rm api bash

docker-shell-web:
	# Shell into the dev container.
	# docker run -it --env-file app/.env --entrypoint bash wps-api_api:latest
	docker-compose run --rm web bash