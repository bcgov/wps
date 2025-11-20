## Weather Model Naming Conventions

### Environment Canada weather model naming conventions

[RDPS](https://eccc-msc.github.io/open-data/msc-data/nwp_rdps/readme_rdps-datamart_en/)\
[GDPS](https://eccc-msc.github.io/open-data/msc-data/nwp_gdps/readme_gdps-datamart_en/)\
[HRDPS](https://eccc-msc.github.io/open-data/msc-data/nwp_hrdps/readme_hrdps-datamart_en/)

### 24 hour accumulated precipitation

Weather models calculate accumulated precipitation since the start of the model run.
For example:
`CMC_reg_APCP_SFC_0_ps10km_2024073100_P003.grib2` indicates 003 hours of precip accumulation from the start
of the model run on 2024-07-31 at 00:00 UTC (2024-07-30 17:00 PDT).

For various fire weather indices, 24 hour accumulated precip is required across the province. To accomplish this
we are differencing weather model grib2 files for specific times 24 hours apart and storing the result as a geotiff.

### Naming convention

- **COMPUTED** : constant string indicating that the data is computed data, not source data.
- **reg** : constant string indicating that the data is from the RDPS. This varies depending on weather model.
- **Variable** : Variable type included in this file. APCP refers to accumulated precipitation.
- **LevelType** : Level type. SFC refers to surface.
- **Level** : Level value. 0 refers to ground level (0 height above ground)
- **ps10km** : constant string indicating that the projection used is polar-stereographic at 10km resolution.
- **YYYYMMDD** : Year, month and day that the 24 hour accumulation refers to.
- **hhz** : The data includes 24 hours of precip accumulation ending at this UTC hour of **YYYYMMDD** [00...23]
- **tif** : constant string indicating the geotiff format is used

**Example**\
Input:\
`2024-07-31/00/precip/CMC_reg_APCP_SFC_0_ps10km_2024073100_P002.grib2`\
`2024-07-31/00/precip/CMC_reg_APCP_SFC_0_ps10km_2024073100_P026.grib2`

Output:\
`2024-08-01/00/precip/COMPUTED_reg_APCP_SFC_0_ps10km_20240801_02z.tif`\
This geotiff contains 24 hours of precip accumulation ending on 2024-08-01 02:00 UTC. The geotiff will be stored according to the date and model run used in the calculation (00 in this case).
