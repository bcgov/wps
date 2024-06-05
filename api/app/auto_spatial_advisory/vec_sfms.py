from numba import vectorize

from app.auto_spatial_advisory.sfms import bui

vec_bui = vectorize(bui)