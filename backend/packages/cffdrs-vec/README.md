# cffdrs_vec

Numba-vectorized wrappers around [cffdrs](https://github.com/cffdrs/cffdrs_py) FWI and FBP functions, for running those calculations over whole rasters/arrays instead of one station/pixel at a time.

The key modules are `fwi.py` and `fbp.py`.

## fwi.py

Vectorizes the six FWI System functions (FFMC, DMC, DC, ISI, BUI, FWI). Each is self-contained (only calls `math`, no other cffdrs functions), so each is just wrapped directly with `numba.vectorize`.

## fbp.py

Vectorizes the FBP System functions used elsewhere in this codebase (`rate_of_spread`, `back_rate_of_spread`, `slope_adjustment`, `total_fuel_consumption`, etc). About half of these are self-contained like the FWI functions above, but the rest call other plain-Python cffdrs functions internally (e.g. `rate_of_spread` → `rate_of_spread_extended` → `surface_fire_rate_of_spread` → `safe_div`), which `numba.vectorize` can't compile through on its own - numba's nopython mode can only call functions it has itself compiled.

To vectorize those too, `fbp.py` `jit`-compiles the whole dependency chain bottom-up and patches each cffdrs module's own namespace so its internal calls resolve to the jitted versions, instead of the original plain-Python ones. A few of the per-fuel-type lookup tables those functions index by `fuel_type_code` (`ROS_A`, `ROS_B`, `ROS_C0`, `BUI_O`) mix Python `int` and `float` literals, which numba types as a heterogeneous tuple indexable only by a compile-time constant - those get patched too, as homogeneous `float64` arrays.

This reaches into cffdrs's private functions and constant tables, so it's coupled to cffdrs's current internal call graph and table names. A cffdrs upgrade that renames or restructures these will raise an `AttributeError` here at import time rather than silently computing wrong values.
