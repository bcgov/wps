# -*- coding: utf-8 -*-
"""
Created on Tue Dec  2 08:05:37 2025

"""

from plot_500hPa_map import plot_500hpa, PLOT_CONFIG
import numpy as np

# Here you can config all the features for the 500mb map

# ---- 500 hPa map configuration (control panel) ----
cfg = PLOT_CONFIG.copy()

# --- Files (only if you want to change them) ---
# cfg["z500_grib"] = "data/another_z500.grib2"
# cfg["vort_grib"] = "data/another_rv500.grib2"

# --- Domain / projection ---
cfg["central_longitude"] = -130.0
cfg["central_latitude"]  = 50.0
cfg["extent"]            = [-170.0, -100.0, 30.0, 75.0]  # [lon_min, lon_max, lat_min, lat_max]

# --- Gridlines / labels ---
cfg["grid_dx"]         = 5        # gridline spacing in deg
cfg["grid_dy"]         = 5        # gridline spacing in deg
cfg["lon_label_value"] = -140   # shows "140W"
cfg["lat_label_value"] = 40     # shows "40N"

# --- 500 hPa heights --- 
cfg["height_interval"]      = 6                 # 6 dam spacing
cfg["height_range"]         = [480, 600]        # min, max dam
cfg["height_highlight"]     = [528, 546, 570]   # bold contours
cfg["height_label_lon"]     = -140.0            # ECCC-style boxed labels along this lon
cfg["height_label_tol"]     = 3.0               # how close (dam) the column must be
cfg["height_label_min_dlat"]= 0.7

# --- Relative vorticity (contours) ---
cfg["vort_levels"]       = list(np.arange(-16, 16, 8))  # you can change to [-20,-10,0,10,20]
cfg["vort_linewidth"]    = 0.5
cfg["vort_linestyle"]    = "dashed"

# --- Vorticity +/- centres ---
cfg["vort_threshold"]     = 0.0     # threshold for + / − centres (1e-5 s^-1)
cfg["vort_window"]        = 39      # neighbourhood size for extrema
cfg["vort_grid_min_dist"] = 6       # gridpoints for first thinning
cfg["vort_deg_min_dist"]  = 1.0     # degrees for second thinning
cfg["vort_symbol_fontsize"] = 5     
cfg["vort_value_fontsize"]  = 5

# --- H/L centres ---
cfg["hl_window"]        = 51        # neighbourhood size for extrema
cfg["hl_grid_min_dist"] = 8         # gridpoints for first thinning
cfg["hl_deg_min_dist"]  = 1.5       # degrees for second thinning
cfg["hl_letter_fontsize"] = 22      # "H" and "L" symbol's fontsize
cfg["hl_value_fontsize"]  = 10      # "H" and "L" value's fontsize

# --- Fire boundary ---
cfg["show_fire_boundary"] = False   # set True if you want to show BCWS boundary
cfg["fire_facecolor"]     = "none"  # set color if you want to show shaded/colored BCWS area
cfg["fire_edgecolor"]     = "0.3"   # set outline color
cfg["fire_linewidth"]     = 1.0     # set outline linewidth

# --- Toggles ---
cfg["show_HL"]           = True
cfg["show_vort_symbols"] = True

# --- Styling ---
cfg["base_fontsize"]  = 7
cfg["axes_linewidth"] = 0.3
cfg["coastline_lw"]   = 0.5
cfg["borders_lw"]     = 0.4
cfg["province_lw"]    = 0.5


# --- Banner ---
cfg["banner_top"]    = "0H FORECAST - PREVISION 0h"
cfg["banner_mid"]    = "V12Z TUE-MAR 02 DEC-DEC 25"
cfg["banner_left"]   = "500 hPa"
cfg["banner_center"] = "HEIGHT-HAUTEUR"
cfg["banner_right"]  = "VORTICITY-TOURBILLON"

cfg["panel_left_top"]    = "GLOBAL"
cfg["panel_left_bottom"] = "GEM"

cfg["legend_left"]   = "HEIGHT - HAUTEUR"
cfg["legend_center"] = "VORTICITY - TOURBILLON"
cfg["legend_right"]  = "+ − ...8, 12, 16... (1.E-5) /s"

cfg["use_banner_header"] = False

# --- Output ---
# optional tight-layout / margin tweaks if your core code uses them
cfg["tight_layout_pad"] = 0.2
cfg["subplots_adjust"] = {
    "left": 0.03,
    "right": 0.97,
    "bottom": 0.03,
    "top": 0.93,
}
cfg["output_dir"]      = "outputs"
cfg["output_filename"] = "GDPS_500hPa_Height_Vorticity_ECCCstyle.png"
cfg["dpi"]             = 300
cfg["figsize"]         = (10, 7)
cfg["title"]           = "GDPS 500 hPa Height (dam) + Relative Vorticity (1e-5 s⁻¹)"


# ---- Generate the plot ----
plot_500hpa(cfg)

