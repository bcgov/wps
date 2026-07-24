from cffdrs import (
    buildup_index,
    drought_code,
    duff_moisture_code,
    fine_fuel_moisture_code,
    fire_weather_index,
)
from cffdrs.fwi import _initial_spread_index
from numba import vectorize

vectorized_bui = vectorize(buildup_index)
vectorized_dc = vectorize(drought_code)
vectorized_dmc = vectorize(duff_moisture_code)
vectorized_ffmc = vectorize(fine_fuel_moisture_code)
# initial_spread_index() now delegates to _initial_spread_index() for its actual
# formula (see cffdrs' vectorization-ready convention); the public wrapper only adds
# range-validating raise ValueError guards, which numba can't compile through, so we
# vectorize the private leaf function directly instead.
vectorized_isi = vectorize(_initial_spread_index)
vectorized_fwi = vectorize(fire_weather_index)
