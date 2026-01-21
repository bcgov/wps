# wps-tools

Utility tools for Wildfire Predictive Services Unit.

Contains utilities for managing raster data, S3 operations, and other administrative tasks.

Assumes installation and setup is done in [backend/README.md](../../README.md)

## Environment Variables

These tools use the standard object store configuration:

- `OBJECT_STORE_SERVER`: S3-compatible endpoint
- `OBJECT_STORE_USER_ID`: Access key ID
- `OBJECT_STORE_SECRET`: Secret access key
- `OBJECT_STORE_BUCKET`: Bucket name
