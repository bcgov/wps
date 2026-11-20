"""Weather model grids over BC, kept in Icechunk alongside the station data, so that a forecast
can be read at any location and a station added later can be given the model's history.

- `grib`: GRIB2 fields as their packed integers, cropped to BC.
- `models`: the models kept, and loading a run of one.
- `store`: `GridStore`, a model's `recent` or `history` store.

Design: docs/architecture/model-grid-storage-spike.md
"""
