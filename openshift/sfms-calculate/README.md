# SFMS Raster Calculation job

Creates a one off job to run SFMS raster calculations for a specific date and hour

## Create job

### Apply template to build the job on Openshift

Example:

```bash
oc process -p DATE="2024-10-10" -p HOUR=5 -p IMAGE_NAME=pr-4042 -f sfms-job.yaml | oc apply -f -
```

DATE is the start date of the calculations
HOUR is the hour for the start date. This determines which model run of data will be used [defaults to 20]
