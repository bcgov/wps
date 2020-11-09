docker-build:
	# Build docker images.
	# NOTE: This will fail outside of the openshift environment, as
	# it references an image stored on docker-registry.default.svc:5000
	docker-compose build

docker-run:
	# Run api in production mode, in docker.
	docker-compose up

docker-build-dev:
	# Build dev docker images.
	# Having issues? try: docker volume prune
	# Still having issues? try: docker system prune
	docker-compose -f docker-compose.dev.yml build

docker-run-dev:
	# Run docker in dev mode.
	docker-compose -f docker-compose.dev.yml up --build
