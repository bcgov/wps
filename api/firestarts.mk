# List datasets available in object store
list-fire-starts-datasets:
	$(POETRY_RUN) python -m app.human_fire_starts.scripts.list_datasets

# Publish datasets (naive, just any file) that exists in app/human_fire_starts/data
publish-fire-starts-datasets:
	$(POETRY_RUN) python -m app.human_fire_starts.scripts.publish_datasets

# Download latest datasets from object store to app/human_fire_starts/data
latest-fire-starts-datasets:
	$(POETRY_RUN) python -m app.human_fire_starts.scripts.get_latest_datasets