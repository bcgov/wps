# -*- coding: utf-8 -*-
"""
Control panel for GDPS MSLP + 1000–500 hPa Thickness map.

Edit values in cfg to change domain, contour levels, shading band,
H/L behaviour, fire boundary, output name, etc., without touching
the core plotting code.
"""

from plot_mslp_thickness_map import plot_mslp_thickness, PLOT_CONFIG
import numpy as np

# ---- MSLP + Thickness map configuration (control panel) ----
cfg = PLOT_CONFIG.copy()

# --------------------------------------------------
# Files (relative to project root)
# --------------------------------------------------
# Change only if your filenames/paths change
# cfg["mslp_grib"]   = "data/20251119T12Z_MSC_GDPS_Pressure_MSL_LatLon0.15_PT000H.grib2"
# cfg["mslp_index"]  = "mslp.idx"
# cfg["thk_grib"]    = "data/20251119T12Z_MSC_GDPS_Thickness_IsbL-1000to0500_LatLon0.15_PT000H.grib2"
# cfg["thk_index"]   = "thk1000_500.idx"
# cfg["fire_outline"] = "fire_centers_all.geojson"

# --------------------------------------------------
# Projection / domain
# --------------------------------------------------
cfg["central_longitude"] = -130.0
cfg["central_latitude"]  = 50.0
# [lon_min, lon_max, lat_min, lat_max]
cfg["extent"]            = [-170.0, -100.0, 30.0, 75.0]

# --------------------------------------------------
# Gridlines / labels
# --------------------------------------------------
cfg["grid_dx"]         = 5                   # gridline spacing in deg
cfg["grid_dy"]         = 5
cfg["lon_label_value"] = -140            # will show "140W"
cfg["lat_label_value"] = 40              # will show "40N"
cfg["label_fontsize"]  = 7
cfg["label_alpha"]     = 0.65

# --------------------------------------------------
# Base map / fire boundary
# --------------------------------------------------
cfg["show_fire_boundary"] = True            # turn BCWS outline on/off
cfg["fire_facecolor"]     = "none"
cfg["fire_edgecolor"]     = "0.3"
cfg["fire_linewidth"]     = 0.4

cfg["coastline_lw"]       = 0.5
cfg["borders_lw"]         = 0.4
cfg["province_lw"]        = 0.5

# --------------------------------------------------
# MSLP contour settings
# --------------------------------------------------
# All MSLP contour levels (hPa)
cfg["mslp_levels"]              = list(np.arange(960, 1050, 4))
cfg["mslp_linewidth"]           = 1.0

# Thicker highlighted MSLP levels (hPa)
cfg["mslp_highlight_levels"]    = [1000, 1024]
cfg["mslp_highlight_linewidth"] = 2.0

# ECCC-style column of boxed MSLP labels
cfg["mslp_label_lon"]           = -140.0   # longitude for vertical stack of labels
cfg["mslp_label_tol"]           = 3.0      # how close (hPa) column must be
cfg["mslp_label_min_dlat"]      = 0.7      # min separation in latitude (deg)
cfg["mslp_label_fontsize"]      = 6

# --------------------------------------------------
# Thickness contour + shaded band
# --------------------------------------------------
# 1000–500 hPa thickness contour levels (dam)
cfg["thk_levels"]          = list(np.arange(480, 600, 6))
cfg["thk_linewidth"]       = 1.0
cfg["thk_linestyle"]       = "dashed"

# Shaded band (e.g. 534–540 dam with hatch)
cfg["shade_band"]          = True
cfg["shade_min"]           = 534          # lower bound (dam)
cfg["shade_max"]           = 540          # upper bound (dam)
cfg["shade_hatch"]         = "....."
cfg["shade_hatch_linewidth"] = 0.15

# Boxed thickness labels along one longitude
cfg["thk_label_lon"]       = -110.0
cfg["thk_label_tol"]       = 3.0
cfg["thk_label_min_dlat"]  = 0.7
cfg["thk_label_fontsize"]  = 6

# --------------------------------------------------
# H / L detection & drawing
# --------------------------------------------------
cfg["show_HL"]          = True

# Local-extrema window and thinning
cfg["hl_window"]        = 57          # neighbourhood size (gridpoints)
cfg["hl_grid_min_dist"] = 8           # thinning in grid space
cfg["hl_deg_min_dist"]  = 1.5         # thinning in degrees

# Geometry of labels around the centre (deg)
cfg["hl_d_letter"]      = 1.5        # letter above centre
cfg["hl_d_value"]       = 1.2        # value below centre
cfg["hl_pad_lon"]       = 1.0        # padding from map edge
cfg["hl_pad_lat"]       = 1.0

# Font sizes and halo widths
cfg["hl_letter_fontsize"]      = 20
cfg["hl_letter_halo_width"]    = 3.0
cfg["hl_center_fontsize"]      = 10
cfg["hl_center_halo_width"]    = 2.0
cfg["hl_value_fontsize"]       = 8
cfg["hl_value_halo_width"]     = 2.0

# --------------------------------------------------
# Styling / figure
# --------------------------------------------------
cfg["base_fontsize"]  = 7
cfg["axes_linewidth"] = 0.3
cfg["figsize"]        = (10, 7)
cfg["dpi"]            = 300

# optional tight-layout / margin tweaks if your core code uses them
cfg["tight_layout_pad"] = 0.2
cfg["subplots_adjust"] = {
    "left": 0.03,
    "right": 0.97,
    "bottom": 0.03,
    "top": 0.93,
}

# --------------------------------------------------
# Output
# --------------------------------------------------
cfg["output_dir"]      = "outputs"
cfg["output_filename"] = "GDPS_small_domain_ECCCstyle.png"
cfg["title"]           = "GDPS MSLP + 1000–500 hPa Thickness (dam)"


# ---- Generate the plot ----
if __name__ == "__main__":
    plot_mslp_thickness(cfg)
