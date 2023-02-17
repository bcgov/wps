# Fetching & Interpreting Weather Model Data

## Table of Contents

## Introduction

Some of the core functionalities of Morecast (versions 1 and 2) require that we regularly fetch weather model data from various sources. These weather models are computer-generated weather forecasts (although for the sake of clarity, throughout this project we refer to them as "weather models", whereas "forecasts" strictly apply to the weather predictions made by human weather forecasters). Third-party organizations run these weather models on their own hardware and publish the output publicly. Morecast then regularly consumes this weather model data and performs additional analysis on it to suit our specific needs.

## GRIB Files

All weather model produce outputs in GRIB file format. [Refer here for a description of what a GRIB file is](https://weather.gc.ca/grib/what_is_GRIB_e.html).

A GRIB file contains one or more raster bands, in which weather data is presented in a grid format. Each raster band corresponds to one weather variable. (For example, temperature data points will be stored in a different raster band to wind speed data points.) In order to coalesce the points on the data grid with geographic locations (such as lat/long coordinates), a geographic coordinate transformation must be applied. This coordinate transformation is performed in our backend, using metadata supplied by the source of the GRIB file.

## Data Sources

### Environment Canada

We fetch GDPS, RDPS, and HRDPS model data from Environment Canada (EC). EC outputs a separate GRIB file for each weather variable, and each GRIB file contains only one raster band. (There are many weather variables available, we only download the files that Morecast needs.)

The GDPS, RDPS, and HRDPS models have different cycle lengths, different resolutions, and different coordinate systems. For example, the [RDPS model](https://weather.gc.ca/grib/grib2_reg_10km_e.html) uses a resolution of 10km projected onto a polar stereographic grid, while the [GDPS model](https://weather.gc.ca/grib/grib2_glb_25km_e.html) uses a 25km resolution on a lat-lon grid. For the [HRDPS model](https://weather.gc.ca/grib/grib2_HRDPS_HR_e.html), we use the Continental domain, which has a resolution of 2.5km on a polar stereographic grid.

#### Relevant Data Links

##### GDPS
- [GDPS weather variables for 0-hour forecasts](https://weather.gc.ca/grib/GLB_HR/GLB_latlonp24xp24_P000_deterministic_e.html)
- [GDPS weather variables for non-zero-hour forecasts](https://weather.gc.ca/grib/GLB_HR/GLB_latlonp24xp24_P003144_03_and_P150168_06_deterministic_e.html)
- [Formatting of filenames (and data download source)](https://weather.gc.ca/grib/grib2_glb_25km_e.html)


##### RDPS
- [RDPS weather variables for 0-hour forecasts](https://weather.gc.ca/grib/REG_HR/REGIONAL_ps10km_P000_deterministic_e.html)
- [RDPS weather variables for non-zero-hour forecasts](https://weather.gc.ca/grib/REG_HR/REGIONAL_ps10km_PNONZERO_deterministic_e.html)
- [Formatting of filenames](https://weather.gc.ca/grib/grib2_reg_10km_e.html)
- [Data download source](https://dd.weather.gc.ca/model_gem_regional/10km/grib2/)

##### HRDPS
- [HRDPS weather variables for 0-hour forecasts](https://weather.gc.ca/grib/HRDPS_HR/HRDPS_nat_ps2p5km_P000_deterministic_e.html)
- [HRDPS weather variables for non-zero-hour forecasts](https://weather.gc.ca/grib/HRDPS_HR/HRDPS_ps2p5km_PNONZERO_deterministic_e.html)
- [Formatting of filenames](https://weather.gc.ca/grib/grib2_HRDPS_HR_e.html)
- [Data download source](https://dd.weather.gc.ca/model_hrdps/continental/grib2/)

#### Relevant Weather Variables

The GDPS, RDPS, and HRDPS weather variables that we currently fetch for use in Morecast are `TMP_TGL_2m` (temperature), `RELH_TGL_2m` (relative humidity), `WIND_TGL_10m` (wind speed), `WDIR_TGL_10m` (wind direction), and `APCP_SFC_0` (accumulated precipitation).

### NOAA

We fetch [GFS model data from NCEP-NOAA](https://www.ncei.noaa.gov/products/weather-climate-models/global-forecast). NOAA outputs only one GRIB file for all weather variables for a specific timestamp, so each of their GRIB files contains hundreds of raster bands, with one raster band for each weather variable. We therefore must download the entire GRIB file, even though we only need data from a small number of the raster bands in the file.

Specifically, we fetch GFS model data on a 0.5&deg; scale, based on the request of staff forecasters. We fetch the data from [this server](https://www.ncei.noaa.gov/data/global-forecast-system/access/grid-004-0.5-degree/forecast/).

## Linear Interpolation

### From grids to fire weather stations

Once model data has been downloaded, we store the model data for "grid subsets" relevant to our use in our `wps` Postgres database in the `model_run_grid_subset_predictions` table. Each row in this table stores temperature, RH, precipitation, wind speed, and wind direction data, as we need for Morecast. For each of these weather variables, each row contains an array of 4 data points, corresponding to the 4 corners of one square of the grid. The `prediction_model_grid_subset_id` in this table corresponds to a grid cell that contains one of BC's fire weather station locations, as stored in the `prediction_model_grid_subsets` table. When our backend inserts data into the `model_run_grid_subset_predictions` table, it also adds metadata pertinent to the specific model run.

Once the `model_run_grid_subset_predictions` table has been populated for a given model run, our backend then performs linear interpolation based on the geographic location of each weather station to calculate an approximated value for each weather variable.

For example, a small portion of the grid for a temperature raster band of a GRIB file might look like the image below. In this example, each point on the grid is spaced 5km apart. You can see that a fire weather station is located within one cell of this grid, where the 4 corners of the cell have temperature values of 3.1&deg;, 2.4&deg;, 2.7&deg;, and 2.7&deg;C. In order to approximate the predicted temperature at the weather station's exact location, we perform linear interpolation of the 4 temperature values listed above, where the weight of each data point is inversely proportional to the distance from the weather station to that point on the grid. Consequently, the 2.4&deg;C from the top right corner of the cell will have the highest weight as it is closest to the weather station, and the 2.7&deg;C from the bottom left corner will have the lowest weight as it is the furthest away.


![Location-based linear interpolation for a weather station](../../../docs/images/Grid_wx_station.png)

This linear interpolation process is repeated for each of the weather variables in a model run, and for each of the weather stations in BC. These calculations are stored in the `weather_station_model_predictions` table.

At the present time we are only performing linear interpolation from grid subsets to weather stations based on geographic distance (because it is the simplest method of interpolation). Forecasters have requested that we also perform linear interpolation based on station elevation as the results may be more accurate - this is a pending story in our backlog.

### To 13:00 PDT

## Cronjobs