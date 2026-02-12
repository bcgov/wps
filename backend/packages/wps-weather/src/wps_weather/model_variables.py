GDPS_RDPS_COMMON = [
    "GeopotentialHeight_IsbL-0500",
    "GeopotentialHeight_IsbL-0700",
    "GeopotentialHeight_IsbL-0850",
    "AbsoluteVorticity_IsbL-0500",
    "Pressure_MSL",
    "Thickness_IsbL-1000to0500",
    "AirTemp_IsbL-0850",
    "AirTemp_AGL-2m",
    "WindU_IsbL-0850",
    "WindV_IsbL-0850",
    "WindU_AGL-10m",
    "WindV_AGL-10m",
    "WindSpeed_IsbL-0250",
    "RelativeHumidity_IsbL-0500",
    "RelativeHumidity_IsbL-0700",
    "RelativeHumidity_IsbL-0850",
    "RelativeHumidity_AGL-2m",
]

GDPS_ONLY = [
    "RelativeVorticity_IsbL-0500",
    "Precip-Accum12h_Sfc",
    "Precip-Accum6h_Sfc",
]

RDPS_ONLY = [
    "Precip-Accum3h_Sfc",
]

GDPS_VARIABLES = GDPS_RDPS_COMMON + GDPS_ONLY
RDPS_VARIABLES = GDPS_RDPS_COMMON + RDPS_ONLY


HRDPS_VARIABLES = []
