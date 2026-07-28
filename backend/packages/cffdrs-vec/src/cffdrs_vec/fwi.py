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
# initial_spread_index() is the only one of the six where cffdrs itself split validation from
# computation into two functions: the public wrapper just validates, then delegates to
# _initial_spread_index() for the formula. numba's nopython mode can't compile a call into a
# second function it hasn't itself compiled, so vectorizing the public wrapper fails; the other
# five are each one self-contained function (guards + math, no delegation), so they vectorize
# fine, guards included.
vectorized_isi = vectorize(_initial_spread_index)
vectorized_fwi = vectorize(fire_weather_index)
