
run:
	# Fetch zones as geojson from esri server
	python -m workers.fetch_zones
	# Import into psql
	./import.sh

fetch-zones:
	# Fetch zones as geojson from esri server
	python -m workers.fetch_zones

import:
	./import.sh