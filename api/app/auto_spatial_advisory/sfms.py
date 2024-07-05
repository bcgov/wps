from cffdrs import bui, dc, dmc
from numba import vectorize

vectorized_bui = vectorize(bui)
vectorized_dc = vectorize(dc)
vectorized_dmc = vectorize(dmc)
