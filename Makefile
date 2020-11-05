docker-build:
	# Build docker images.
	docker-compose build

docker-run:
	# Run api in production mode, in docker.
	docker-compose up