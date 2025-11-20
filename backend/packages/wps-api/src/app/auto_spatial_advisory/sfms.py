from cffdrs import bui, dc, dmc, ffmc, fwi, isi
from numba import vectorize

vectorized_bui = vectorize(bui)
vectorized_dc = vectorize(dc)
vectorized_dmc = vectorize(dmc)
vectorized_ffmc = vectorize(ffmc)
vectorized_isi = vectorize(isi)
vectorized_fwi = vectorize(fwi)
