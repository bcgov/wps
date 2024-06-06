from cffdrs import bui
from numba import vectorize

vectorized_bui = vectorize(bui)