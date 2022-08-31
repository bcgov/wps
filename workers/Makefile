
run:
	# Fetch zones as geojson from esri server
	python -m workers.fetch_zones
	# Import into psql
	./import.sh

fetch-zones:
	# Fetch zones as geojson from esri server
	python -m workers.fetch_zones

simplify-zones:
	# Simplify zones as geojson from esri server
	python -m workers.simplify_zones

import:
	./import.sh