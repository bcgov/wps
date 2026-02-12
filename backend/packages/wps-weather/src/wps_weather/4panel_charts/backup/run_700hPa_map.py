# -*- coding: utf-8 -*-
"""
Control panel for GDPS 700 hPa Height + 850–700–500 hPa Humidity map.

Edit cfg below to tweak levels, shading, domain, etc.,
without changing the core plotting code.
"""

import numpy as np
from plot_700hPa_map import plot_700hpa, PLOT_CONFIG_700

# Start from defaults
cfg = PLOT_CONFIG_700.copy()

# --- Optionally change file names (if your GRIB names differ) ---
# cfg["z700_grib"] = "data/your_700_height_file.grib2"
# cfg["rh_grib"]   = "data/your_layer_humidity_file.grib2"

# --- Domain / projection ---
cfg["central_longitude"] = -130.0
cfg["central_latitude"]  = 50.0
cfg["extent"]            = [-170.0, -100.0, 30.0, 75.0]

# --- Gridlines / labels ---
cfg["grid_dx"]         = 5
cfg["grid_dy"]         = 5
cfg["lon_label_value"] = -140  # 140W
cfg["lat_label_value"] = 40     # 40N

# --- 700 hPa heights ---
cfg["height_interval"]      = 6
cfg["height_range"]         = [240, 330]
cfg["height_highlight"]     = [276, 300]  # bold
cfg["height_label_levels"]  = list(np.arange(264, 320, 6))
cfg["height_label_lon"]     = -140.0
cfg["height_label_tol"]     = 3.0
cfg["height_label_min_dlat"]= 0.7

# --- Humidity field (contours) ---
cfg["rh_levels"]    = [50, 70, 90]
cfg["rh_linewidth"] = 1
cfg["rh_linestyle"] = "dashed"
cfg["rh_label_levels"] = [50, 70, 90]
cfg["rh_label_lons"]    = [-165.0,-160.0, -150.0,-145.0, -130.0, -115.0, -100.0]
cfg["rh_label_tol"]    = 2.0
cfg["rh_label_min_dlat"] = 0.7

# --- Shaded bands (dot hatches) ---
cfg["shade_70_90"]          = True
cfg["shade_90_plus"]        = True
cfg["shade_70_90_hatch"]    = "...."      # lighter dots
cfg["shade_90_plus_hatch"]  = "......."    # denser dots
cfg["shade_edge_lw"]        = 0.6
cfg["shade_hatch_lw"]       = 0.15
cfg["shade_70_color"]       = "#c6e8b5"    # Humidity 70% area color
cfg["shade_90_color"]       = "#a8d8f0"    # Humidity 90% area color

# --- H/L centres (700 hPa) ---
cfg["show_HL"]            = True
cfg["hl_window"]          = 51
cfg["hl_grid_min_dist"]   = 8
cfg["hl_deg_min_dist"]    = 1.5
cfg["hl_d_letter"]        = 1.5
cfg["hl_d_value"]         = 1.2
cfg["hl_pad_lon"]         = 1.0
cfg["hl_pad_lat"]         = 1.0
cfg["hl_letter_fontsize"] = 22
cfg["hl_center_fontsize"] = 10
cfg["hl_value_fontsize"]  = 8

# --- Fire boundary ---
cfg["show_fire_boundary"] = False  # turn on if you want BCWS outline
cfg["fire_facecolor"]     = "none"
cfg["fire_edgecolor"]     = "0.3"
cfg["fire_linewidth"]     = 1.0

# --- Styling / figure ---
cfg["figsize"]        = (10, 7)
cfg["dpi"]            = 300
cfg["title"]          = "GDPS 700 hPa Height (dam) + 850–700–500 hPa Humidity (%)"
cfg["subplots_adjust"] = {
    "left": 0.03,
    "right": 0.97,
    "bottom": 0.03,
    "top": 0.93,
}
cfg["tight_layout_pad"] = 0.2

# --- Output ---
cfg["output_dir"]      = "outputs"
cfg["output_filename"] = "GDPS_700hPa_Height_Humidity_ECCCstyle.png"

# ---- Run ----
if __name__ == "__main__":
    plot_700hpa(cfg)
