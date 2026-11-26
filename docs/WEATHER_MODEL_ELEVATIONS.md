# Weather model surface elevations

Model elevations are sampled at station locations using the same grid cells as weather predictions.

Canadian model fields come from [ECCC Datamart](https://dd.weather.gc.ca/today/),
GFS from [NOAA NOMADS](https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl),
and ECMWF from [ECMWF Open Data](https://data.ecmwf.int/forecasts/) and its public mirrors.

| Model | Grid | Surface field | Forecast lead in hours |
| --- | --- | --- | --- |
| HRDPS | Continental 2.5 km | `HGT_Sfc` | 1 |
| RDPS | 10 km | `GeopotentialHeight_Sfc` | 0 |
| GDPS | 15 km | `GeopotentialHeight_Sfc` | 0 |
| GFS | 0.25 degrees, BC subset | Surface `HGT` | 0 |
| ECMWF | IFS `oper`, 0.1 degrees | Surface geopotential `z` | 0 |

Canadian and GFS fields already contain heights in metres or geopotential metres.
ECMWF geopotential is divided by `9.80665` to obtain geopotential height in metres.
No vertical datum correction is applied when comparing model and station elevations.
