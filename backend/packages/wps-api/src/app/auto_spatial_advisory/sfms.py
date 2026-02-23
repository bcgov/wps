from cffdrs import buildup_index, drought_code, duff_moisture_code, fine_fuel_moisture_code, fire_weather_index, initial_spread_index
from numba import vectorize

vectorized_bui = vectorize(buildup_index)
vectorized_dc = vectorize(drought_code)
vectorized_dmc = vectorize(duff_moisture_code)
vectorized_ffmc = vectorize(fine_fuel_moisture_code)
vectorized_isi = vectorize(initial_spread_index)
vectorized_fwi = vectorize(fire_weather_index)
