from cffdrs import bui, dc, dmc, ffmc
from numba import vectorize

vectorized_bui = vectorize(bui)
vectorized_dc = vectorize(dc)
vectorized_dmc = vectorize(dmc)
vectorized_ffmc = vectorize(ffmc)
