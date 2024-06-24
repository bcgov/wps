"""
Reading and writing of RDPS URLs, based on the specification here:
https://eccc-msc.github.io/open-data/msc-data/nwp_rdps/readme_rdps-datamart_en/#filename-nomenclature
"""

from datetime import datetime

# Canadian Meterological Centre constant
CMC = "CMC"
# RDPS constant
REG = "reg"
# Accumulating precipitation constant
APCP = "APCP"
# Surface level type
SFC = "SFC"
# Level 0
LEVEL = "0"
# Polar-stereographic projection at 10km resolution
PS10KM = "ps10km"
# Grib2 file type
GRIB2 = "grib2"
# Filename delimiter
DELIMITER = "_"
# Possible run hours
RUN_HOURS = ["00", "06", "12", "18"]
# Possible forecast hours
FORECAST_HOURS = [f"{hour:03d}" for hour in list(range(0, 84))]


def parse_rdps_filename(url: str):
    """Parse and return the forecast start date and run hour from the RDPS grib url."""
    tokens = url.split(DELIMITER)
    assert tokens[0] == CMC
    assert tokens[1] == REG
    assert tokens[2] == APCP
    assert tokens[3] == SFC
    assert tokens[4] == LEVEL
    assert tokens[5] == PS10KM

    # utc datetime in YYYYMMDDHH format
    assert len(tokens[6]) == 10
    forecast_start_date = tokens[6][:-2]
    run_hour = tokens[6][-2:]
    assert run_hour in RUN_HOURS

    # forecast hour and grib2 file ext
    assert len(tokens[7]) == 10
    final_tokens = tokens[7].split(".")
    assert len(final_tokens) == 2
    # strip off constant 'P', get forecast hours triplet
    forecast_hour = final_tokens[0][-3:]
    assert forecast_hour in FORECAST_HOURS

    return (forecast_start_date, run_hour, forecast_hour)


def compose_rdps_filename(forecast_start_date: datetime, run_hour: int, forecast_hour: int):
    """Compose and return an RDPS url given a forecast start date, run hour and forecast hour."""
    assert forecast_start_date.tzinfo is not None
    assert forecast_start_date.utcoffset().total_seconds() == 0
    assert f"{run_hour:02d}" in RUN_HOURS
    assert f"{forecast_hour:03d}" in FORECAST_HOURS

    return (
        f"{CMC}{DELIMITER}{REG}{DELIMITER}{APCP}{DELIMITER}{SFC}{DELIMITER}{LEVEL}{DELIMITER}{PS10KM}{DELIMITER}"
        f"{forecast_start_date.date().isoformat().replace('-','')}{run_hour:02d}{DELIMITER}P{forecast_hour:03d}.grib2"
    )
