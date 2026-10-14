
docker-build:
	# Build dev docker images.
	# Having issues? try: docker volume prune
	# Still having issues? try: docker system prune
	docker compose build

docker-run:
	# Run docker in dev mode.
	docker compose up

docker-db:
	# Run the database
	docker compose up db

docker-web-server-build:
	# Build the web in server mode (same dockerfile as used in production)
	docker build -f ./Dockerfile.web --tag=wps/web .

docker-web-server:
	# Run the web in server mode (same dockerfile as used in production)
	docker run -p 3000:3000 wps/web

docker-shell-api:
	# Shell into the running dev container.
	docker compose exec api bash

docker-shell-web:
	# Shell into the running dev container.
	# docker run -it --env-file app/.env --entrypoint bash wps-api_api:latest
	docker compose exec web bash

local-object-store-up:
	# start the loopback-only local object store and create empty application buckets
	docker compose -f compose.object-store.yml up -d --wait

local-object-store-down:
	# stop the local object store while preserving its data volume
	docker compose -f compose.object-store.yml down

local-object-store-reset:
	# delete all local object-store data, restart the service, and recreate empty buckets
	docker compose -f compose.object-store.yml down --volumes
	$(MAKE) local-object-store-up
