import requests
import shutil
import os
from datetime import datetime

# The hour of interest as a string at which the model was run (HRDPS and RDPS 00, 06, 12, 18; GDPS 00, 12 )
RUN = '00'
# The Environment Canada numeric weather model of interest (eg. HRDPS, RDPS GDPS)
MODEL = 'GDPS'
# The weather variable of interest.
# RDPS and GDPS values include 'TMP_TGL_2', 'RH_TGL_2', 'APCP_SFC_0', 'WDIR_TGL_10', 'WIND_TGL_10'
# HRDPS values include 'TMP_AGL-2m', 'APCP_Sfc', 'WDIR_AGL-10m', 'WIND_AGL-10m', 'RH_AGL-2m'
GRIB_LAYER = 'APCP_SFC_0'
# A multiplication factor to convert twind speed in m/s to kph
FACTOR = 3.6 if GRIB_LAYER == 'WIND_AGL-10m' or GRIB_LAYER == 'WIND_TGL_10' else 1


def get_date():
    today = datetime.now()
    year = today.strftime('%Y')
    month = today.strftime('%m')
    day = today.strftime('%d')
    return f'{year}{month}{day}'


def download_gdps_grib_files():
    # Naively downloads a gdps grib file and writes it to the directory this script was run from
    for h in range(0, 241, 3):
        hhh = format(h, '03d')
        gdps_base_url = f'https://dd.weather.gc.ca/model_gem_global/15km/grib2/lat_lon/{RUN}/{hhh}/'
        gdps_fname = f'CMC_glb_{GRIB_LAYER}_latlon.15x.15_{get_date()}{RUN}_P{hhh}.grib2'
        # https: // dd.weather.gc.ca / model_gem_global / 15km / grib2 / lat_lon / 00 / 003 / CMC_glb_APCP_SFC_0_latlon.15x.15_2023081500_P003.grib2
        # https: // dd.weather.gc.ca / model_gem_global / 15km / grib2 / lat_lon / 00 / 000 / CMC_glb_APCP_SFC_0_latlon.15x.15_2023081400_P000.grib2
        gdps_grib_url = f'{gdps_base_url}{gdps_fname}'
        print(f'URL: {gdps_grib_url}')
        with requests.get(gdps_grib_url, stream=True) as r:
            with open(f'{gdps_fname}', 'wb') as f:
                shutil.copyfileobj(r.raw, f)


def get_gdps_value_at_location():
    # Writes grib values at the given coordinates to the console

    # Default to Honna station
    coord_x = -132.11561  # longitude
    coord_y = 53.25317  # latitude

    for h in range(0, 241, 3):
        hhh = format(h, '03d')
        fname = f'CMC_glb_{GRIB_LAYER}_latlon.15x.15_{get_date()}{RUN}_P{hhh}.grib2'
        cmd = f"gdallocationinfo {fname} -valonly -wgs84 {coord_x} {coord_y}"
        result = os.popen(cmd).read()
        if result == '':
            print(f'{hhh}: empty')
        else:
            print(f"{hhh}: {round(float(result)*FACTOR, 1)}")


def main():
    download_gdps_grib_files()
    get_gdps_value_at_location()


if __name__ == '__main__':
    main()
