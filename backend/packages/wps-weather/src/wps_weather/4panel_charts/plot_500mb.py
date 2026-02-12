# -*- coding: utf-8 -*-
"""
GDPS 500 hPa Height (dam) + Relative Vorticity (1e-5 s^-1).
Supports:
- Standalone plot (creates fig/ax + saves PNG)
- Multi-panel mode (draws onto provided ax)
"""

import os
from pathlib import Path
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.patheffects as PathEffects

import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.feature import NaturalEarthFeature, ShapelyFeature

from scipy.ndimage import maximum_filter, minimum_filter
import geopandas as gpd
import matplotlib.patches as mpatches

# --------------------------------------------------
# FINAL "decided" feature values live here
# --------------------------------------------------
CFG_500 = {
    # --- Input files ---
    "z500_grib": "data/20251121T12Z_MSC_GDPS_GeopotentialHeight_IsbL-0500_LatLon0.15_PT000H.grib2",
 #   "z500_index": "z500.idx",
    "vort_grib": "data/20251121T12Z_MSC_GDPS_RelativeVorticity_IsbL-0500_LatLon0.15_PT000H.grib2",
 #   "vort_index": "rv500.idx",
    "valid_time_str": "F000 Valid: Tue 2025-11-21 12z",
    "fire_outline": "fire_centers_all.geojson",

    # --- Domain / projection ---
    "central_longitude": -130.0,
    "central_latitude": 50.0,
    "extent": [-170.0, -100.0, 30.0, 75.0],

    # --- Gridlines ---
    "grid_dx": 10,
    "grid_dy": 10,
    "lon_label_value": -140,
    "lat_label_value": 40,

    # --- 500 hPa heights ---
    "height_interval": 6,
    "height_range": [480, 600],
    #"height_highlight": [528, 546, 570],  # bold contours
    "height_highlight": [528, 546],        # bold (default color)
    "height_highlight_red": [570],         # bold + red
    "height_label_lon": -140.0,
    "height_label_tol": 3.0,
    "height_label_min_dlat": 0.7,

    # --- Vorticity ---
    "vort_levels": list(np.arange(4, 32, 4)),
    "vort_colors": [
        "#041836", "#08306B", "#08519C", "#2171B5", "#4292C6",
        "#6BAED6", "#9ECAE1", "#C6DBEF", "#DEEBF7", "#F7FBFF",
        "#FFFFC0",  # lightest yellow (was #FFF3A0)
        "#FFE779",  # second yellow (average)
        "#FFD033",  # third colour stays same
        "#FFC000",
        "#FF9A00", "#FF7400", "#FF4A2D", "#E53935", "#B71C1C", "#7F0000"
        ],
    "vort_linewidth": 0.5,
    "vort_linestyle": "dashed",

    # --- Vort symbols (+/-) ---
    "vort_threshold": 0.0,
    "vort_window": 39,
    "vort_grid_min_dist": 6,
    "vort_deg_min_dist": 1.0,
    "vort_symbol_fontsize": 5,
    "vort_value_fontsize": 5,
    
#     # --- Vort shading bands ---
#     "vort_shading_bands": [
#     (-50, -45, "shade_m50_m45"),
#     (-45, -40, "shade_m45_m40"),
#     (-40, -35, "shade_m40_m35"),
#     (-35, -30, "shade_m35_m30"),
#     (-30, -25, "shade_m30_m25"),
#     (-25, -20, "shade_m25_m20"),
#     (-20, -15, "shade_m20_m15"),
#     (-15, -10, "shade_m15_m10"),
#     (-10, -5,  "shade_m10_m05"),
#     (-5,  0,   "shade_m05_00"),

#     (0, 5,   "shade_00_05"),
#     (5, 10,  "shade_05_10"),
#     (10, 15, "shade_10_15"),
#     (15, 20, "shade_15_20"),
#     (20, 25, "shade_20_25"),
#     (25, 30, "shade_25_30"),
#     (30, 35, "shade_30_35"),
#     (35, 40, "shade_35_40"),
#     (40, 45, "shade_40_45"),
#     (45, 50, "shade_45_50"),
# ],

#     # --- Vorticity shading colours --- 
#     "shade_m50_m45": True,     #       "shade_m50_m45_color": "#041836",  
#     "shade_m45_m40": True,      #      "shade_m45_m40_color": "#08306B",
#     "shade_m40_m35": True,       #     "shade_m40_m35_color": "#08519C",
#     "shade_m35_m30": True,     #       "shade_m35_m30_color": "#2171B5",
#     "shade_m30_m25": True,      #      "shade_m30_m25_color": "#4292C6",
#     "shade_m25_m20": True,       #     "shade_m25_m20_color": "#6BAED6",
#     "shade_m20_m15": True,     #       "shade_m20_m15_color": "#9ECAE1",
#     "shade_m15_m10": True,      #      "shade_m15_m10_color": "#C6DBEF",
#     "shade_m10_m05": True,       #     "shade_m10_m05_color": "#DEEBF7",
#     "shade_m05_00": True,      #       "shade_m05_00_color": "#F7FBFF",

#     "shade_00_05": True, # "shade_00_05_color": "#FFFFD4",  # light yellow
#     "shade_05_10": True, #"shade_05_10_color": "#FFF8A0",  # medium yellow
#     "shade_10_15": True, #"shade_10_15_color": "#FFD033",  # strong yellow
#     "shade_15_20": True, #"shade_15_20_color": "#FFC000",  # yellow-orange transition
#     "shade_20_25": True, #"shade_20_25_color": "#FF9A00",  # orange
#     "shade_25_30": True, #"shade_25_30_color": "#FF7400",  # deep orange
#     "shade_30_35": True, #"shade_30_35_color": "#FF4A2D",  # orange-red
#     "shade_35_40": True, #"shade_35_40_color": "#E53935",  # red
#     "shade_40_45": True, #"shade_40_45_color": "#B71C1C",  # dark red
#     "shade_45_50": True, #"shade_45_50_color": "#7F0000",  # very dark red (near brown)

    # --- H/L centres ---
    "hl_window": 51,        
    "hl_grid_min_dist": 8,
    "hl_deg_min_dist": 1.5,
    "hl_letter_fontsize": 22,
    "hl_value_fontsize": 10,

    # --- Fire boundary ---
    "show_fire_boundary": False,
    "fire_facecolor": "none",
    "fire_edgecolor": "0.3",
    "fire_linewidth": 1.0,

    # --- Toggles ---
    "show_HL": True,
    "show_vort_symbols": True,

    # --- Styling ---
    "base_fontsize": 7,
    "axes_linewidth": 0.3,
    "coastline_lw": 0.5,
    "borders_lw": 0.4,
    "province_lw": 0.5,


    # --- Output (used only in standalone mode) ---
    "output_dir": "outputs",
    "output_filename": "GDPS_500hPa_Height_Vorticity.png",
    "dpi": 300,
    "figsize": (10, 7),
    "title": "GDPS 500 hPa Height (dam) + Relative Vorticity (1e-5 s⁻¹)",
}


# --------------------------------------------------
# Helpers
# --------------------------------------------------
def get_project_root():
    if "__file__" in globals():
        return Path(__file__).resolve().parents[1]
    cwd = Path(os.getcwd()).resolve()
    if cwd.name == "src":
        return cwd.parent
    return cwd


def open_ds(grib_path: Path):
    grib_path = Path(grib_path)
    idx_path = grib_path.with_suffix(grib_path.suffix + ".idx")
    return xr.open_dataset(
        grib_path,
        engine="cfgrib",
        backend_kwargs={"indexpath": str(idx_path)},
    )


def thin_pts(iy, ix, min_dist=8):
    kept = []
    for j in range(len(iy)):
        y, x = iy[j], ix[j]
        if all((y - iy[k])**2 + (x - ix[k])**2 >= min_dist**2 for k in kept):
            kept.append(j)
    return kept


def further_thin_latlon(iy_sub, ix_sub, lat_idx, lon_idx, lats_1d, lon_plot, Z, min_deg=1.5):
    pts = []
    for iy_s, ix_s in zip(iy_sub, ix_sub):
        iy_g = lat_idx[iy_s]
        ix_g = lon_idx[ix_s]
        lat = float(lats_1d[iy_g])
        lon = float(lon_plot[ix_g])
        val = float(Z[iy_g, ix_g])
        pts.append((val, iy_s, ix_s, lat, lon))
    pts.sort(reverse=True, key=lambda x: x[0])

    kept, kept_latlon = [], []
    for val, iy_s, ix_s, lat, lon in pts:
        if any((lat-klat)**2 + ((lon-klon)*np.cos(np.radians((lat+klat)/2)))**2 < min_deg**2
               for klat, klon in kept_latlon):
            continue
        kept.append((iy_s, ix_s))
        kept_latlon.append((lat, lon))
    return kept


def further_thin_vort(iy_sub, ix_sub, lat_idx, lon_idx, lats_1d, lon_plot, V_field, min_deg=1.0, positive=True):
    pts = []
    for iy_s, ix_s in zip(iy_sub, ix_sub):
        iy_g = lat_idx[iy_s]
        ix_g = lon_idx[ix_s]
        lat = float(lats_1d[iy_g])
        lon = float(lon_plot[ix_g])
        val = float(V_field[iy_s, ix_s])
        pts.append((val, iy_s, ix_s, lat, lon))

    pts.sort(reverse=positive, key=lambda x: x[0]) if positive else pts.sort(key=lambda x: x[0])

    kept, kept_latlon = [], []
    for val, iy_s, ix_s, lat, lon in pts:
        if any((lat-klat)**2 + ((lon-klon)*np.cos(np.radians((lat+klat)/2)))**2 < min_deg**2
               for klat, klon in kept_latlon):
            continue
        kept.append((iy_s, ix_s))
        kept_latlon.append((lat, lon))
    return kept


def draw_HL(ax, lon, lat, letter, val, pc, lon_min, lon_max, lat_min, lat_max, cfg):
    d_letter = 1.5
    d_value = 1.2
    lat_letter = lat + d_letter
    lat_value = lat - d_value

    pad_lon, pad_lat = 1.0, 1.0
    if (lon < lon_min+pad_lon or lon > lon_max-pad_lon or
        lat_letter > lat_max-pad_lat or lat_value < lat_min+pad_lat):
        return

    txt = ax.text(lon, lat_letter, letter, transform=pc, ha="center", va="center",
                  fontsize=cfg["hl_letter_fontsize"], fontweight="bold", color="black", zorder=12)
    txt.set_path_effects([PathEffects.Stroke(linewidth=3, foreground="white"), PathEffects.Normal()])

    circ = ax.text(lon, lat, "⊗", transform=pc, ha="center", va="center",
                   fontsize=10, color="black", zorder=12)
    circ.set_path_effects([PathEffects.Stroke(linewidth=2, foreground="white"), PathEffects.Normal()])

    num = ax.text(lon, lat_value, f"{int(val)}", transform=pc, ha="center", va="center",
                  fontsize=cfg["hl_value_fontsize"], fontweight="bold", color="black", zorder=12)
    num.set_path_effects([PathEffects.Stroke(linewidth=2, foreground="white"), PathEffects.Normal()])


def draw_vort_symbol(ax, lon, lat, sign, value, pc, lon_min, lon_max, lat_min, lat_max, cfg):
    # # Skip positive vorticity values on plot
    # if sign == "+":
    #     return
    pad = 0.5
    if not (lon_min+pad <= lon <= lon_max-pad and lat_min+pad <= lat <= lat_max-pad):
        return

    fs_s = cfg["vort_symbol_fontsize"]
    fs_v = cfg["vort_value_fontsize"]

    txt = ax.text(lon, lat+0.4, sign, transform=pc, ha="center", va="center",
                  fontsize=fs_s, color="black", zorder=10)
    txt.set_path_effects([PathEffects.Stroke(linewidth=1.8, foreground="white"), PathEffects.Normal()])

    val_txt = ax.text(lon, lat-0.3, f"{int(abs(value))}", transform=pc, ha="center", va="center",
                      fontsize=fs_v, color="black", zorder=10)
    val_txt.set_path_effects([PathEffects.Stroke(linewidth=1.5, foreground="white"), PathEffects.Normal()])



# --------------------------------------------------
# Main plotter
# --------------------------------------------------
def plot_500hpa(cfg=None, ax=None):
    if cfg is None:
        cfg = CFG_500
    ROOT = get_project_root()
    OUTDIR = ROOT / cfg["output_dir"]
    OUTDIR.mkdir(exist_ok=True)

    plt.rcParams["font.size"] = cfg["base_fontsize"]
    plt.rcParams["axes.linewidth"] = cfg["axes_linewidth"]

    pc = ccrs.PlateCarree()
    proj = ccrs.LambertConformal(central_longitude=cfg["central_longitude"],
                                 central_latitude=cfg["central_latitude"])

    standalone = (ax is None)
    if standalone:
        fig = plt.figure(figsize=cfg["figsize"])
        ax = plt.axes(projection=proj)
        ax.set_title(cfg["title"], fontsize = 10)
    else:
        fig = ax.figure  # for banner if you later want
        ax.set_title("")

    lon_min, lon_max, lat_min, lat_max = cfg["extent"]
    ax.set_extent(cfg["extent"], crs=pc)

    # --- Load data ---
    ds_z500 = open_ds(ROOT / cfg["z500_grib"])
    ds_vort = open_ds(ROOT / cfg["vort_grib"])

    try:
       z = ds_z500[list(ds_z500.data_vars)[0]].squeeze().values
       v = ds_vort[list(ds_vort.data_vars)[0]].squeeze().values
       lats = ds_z500["latitude"].values
       lons = ds_z500["longitude"].values
    finally:
       ds_z500.close()
       ds_vort.close()

    # height to dam
    H500 = z/10.0 if float(z.max()) > 1000 else z

    # vort to 1e-5 s^-1
    vort = v * 1e5

    
    lon_wrapped = ((lons + 180.0) % 360.0) - 180.0
    order = np.argsort(lon_wrapped)
    lon_plot = lon_wrapped[order]

    Z = H500[:, order]
    V = vort[:, order]
    
    # --- Gridlines + single labels ---
    gl = ax.gridlines(draw_labels=False, crs=pc, color="black", linewidth=0.4,
                      alpha=0.4, linestyle="dotted", zorder=1)
    gl.xlocator = mticker.FixedLocator(np.arange(-180, 181, cfg["grid_dx"]))
    gl.ylocator = mticker.FixedLocator(np.arange(0, 91, cfg["grid_dy"]))

    ax.text(cfg["lon_label_value"], lat_max-1.5, f"{abs(cfg['lon_label_value'])}W",
            transform=pc, fontsize=7, alpha=0.65, ha="center", va="center")
    ax.text(lon_min+1.5, cfg["lat_label_value"], f"{cfg['lat_label_value']}N",
            transform=pc, fontsize=7, alpha=0.65, ha="center", va="center")

    # --- Base map ---
    ax.add_feature(cfeature.LAND, edgecolor="black", facecolor="white", linewidth=0.4, zorder=0)
    ax.add_feature(cfeature.COASTLINE, linewidth=cfg["coastline_lw"], zorder=12)
    ax.add_feature(cfeature.BORDERS, linewidth=cfg["borders_lw"], zorder=12)

    provinces = NaturalEarthFeature("cultural", "admin_1_states_provinces_lines", "50m", facecolor="none")
    ax.add_feature(provinces, edgecolor="black", linewidth=cfg["province_lw"], zorder=13)

    if cfg["show_fire_boundary"]:
        try:
            fire_gdf = gpd.read_file(ROOT / cfg["fire_outline"])
            fire_feature = ShapelyFeature(fire_gdf.geometry, crs=pc)
            ax.add_feature(fire_feature, facecolor=cfg["fire_facecolor"], edgecolor=cfg["fire_edgecolor"],
                           linewidth=cfg["fire_linewidth"], zorder=7)
        except Exception as e:
            print("Warning: fire boundary not drawn:", e)

        # Vorticity shading patches
   # bands = cfg["vort_shading_bands"]
 

    # --- Hard mask border (drawn in axes coordinates) ---

    frame = mpatches.Rectangle(
        (0, 0), 1, 1,
        transform=ax.transAxes,
        fill=False,
        edgecolor="black",
        linewidth=1.5,
        zorder=19
    )
    ax.add_patch(frame)
        
#     def add_vorticity_shading_legend(ax, cfg):
#         """
#         Add a discrete legend for relative vorticity shading
#         in the upper-right corner of the map.
#         """
#         def format_vort_label(vmin, vmax):
#             if vmin <= cfg["vort_levels"][0]:
#                 return f"< {cfg['vort_levels'][1]}"
#             elif vmax >= cfg["vort_levels"][-1]:
#                 return f"> {cfg['vort_levels'][-2]}"
#             else:
#                 return f"{vmin}–{vmax}"

#         levels = cfg["vort_levels"]
#         colors = cfg["vort_colors"]
        
#         legend_items = []

#         # Create one patch per band
#         for i in range(len(levels)-1):
#             vmin = levels[i]
#             vmax = levels[i+1]
#             color = colors[i]
#             legend_items.append(
#                 Patch(
#                     facecolor=color,
#                     edgecolor="black",
#                     linewidth=0.3,
#                     label=format_vort_label(vmin, vmax)
#                     )
#                 )

#         legend_items.reverse() #legend_items = [::-1]
#         if not legend_items:
#             return

#         leg = ax.legend(
#             handles=legend_items,
#             title="Rel. Vorticity\n(1×10⁻⁵ s⁻¹)",
#             loc="upper right",
#             frameon=True,
#             framealpha=1.0,
#             fontsize=6,
#             title_fontsize=6,
#             borderpad=0.6,
#             labelspacing=0.3,
#             handlelength=1.2,
#             handleheight=0.8,
#         )

#         # Force legend above all
#         leg.set_zorder(1000)
#         frame = leg.get_frame()
#         frame.set_edgecolor("black")
#         frame.set_linewidth(0.6)
#         frame.set_facecolor("white")
        
#     ax.contourf(
#     lon_plot, lats, V,
#     levels=cfg["vort_levels"],
#     colors=cfg["vort_colors"],
#     extend="both", 
#     transform=pc,
#     antialiased=False,
#     zorder=3
# )
        
    # # --- Call vorticity legend ---
    # add_vorticity_shading_legend(ax, cfg)
        
    # --- Height contours ---
    hmin, hmax = cfg["height_range"]
    hlev = np.arange(hmin, hmax, cfg["height_interval"])

    highlight_h = cfg.get("height_highlight", [])
    highlight_h_red = cfg.get("height_highlight_red", [])

    # Base contours
    ax.contour(
        lon_plot, lats, Z,
        levels=hlev,
        colors="black",
        linewidths=1.0,
        transform=pc,
        zorder=5
        )

    # Bold black highlights (e.g. 528, 546)
    if highlight_h:
        ax.contour(
            lon_plot, lats, Z,
            levels=highlight_h,
            colors="black",
            linewidths=2.0,
            transform=pc,
            zorder=6
            )
    # --- 570 dam special styling ---
    if highlight_h_red:
        # black casing
        ax.contour(
            lon_plot, lats, Z,
            levels=highlight_h_red,
            colors="black",
            linewidths=2.4,
            transform=pc,
            zorder=6
            )

    # boxed labels along one longitude
    idx_lon = np.argmin(np.abs(lon_plot - cfg["height_label_lon"]))
    lat_mask = (lats >= lat_min) & (lats <= lat_max)
    lats_sub = lats[lat_mask]
    Z_col = Z[:, idx_lon][lat_mask]

    used = []
    for lev in hlev:
        iy = int(np.argmin(np.abs(Z_col - lev)))
        if float(np.abs(Z_col[iy] - lev)) > cfg["height_label_tol"]:
            continue
        lat_lab = float(lats_sub[iy])
        if any(abs(lat_lab-u) < cfg["height_label_min_dlat"] for u in used):
            continue
        used.append(lat_lab)
        ax.text(cfg["height_label_lon"], lat_lab, f"{int(lev)}", transform=pc,
                ha="center", va="center", fontsize=8, fontweight="bold",color="white",
                bbox=dict(boxstyle="square,pad=0.1", facecolor="black",
                          edgecolor="black", linewidth=0.6),
                zorder=20)

    # --- Vorticity contours ---
    ax.contour(lon_plot, lats, V, levels=np.array(cfg["vort_levels"]),
               colors="black", linewidths=cfg["vort_linewidth"],
               linestyles=cfg["vort_linestyle"], transform=pc, zorder=4)

    # --- H/L + vort centres ---
    lat_mask_full = (lats >= lat_min) & (lats <= lat_max)
    lon_mask_full = (lon_plot >= lon_min) & (lon_plot <= lon_max)
    lat_idx = np.where(lat_mask_full)[0]
    lon_idx = np.where(lon_mask_full)[0]

    Z_sub = Z[np.ix_(lat_idx, lon_idx)]
    V_sub = V[np.ix_(lat_idx, lon_idx)]

    if cfg["show_HL"]:
        win = cfg["hl_window"]
        zmax = maximum_filter(Z_sub, size=win)
        zmin = minimum_filter(Z_sub, size=win)
        hi = np.where(Z_sub == zmax)
        lo = np.where(Z_sub == zmin)

        hi_k = thin_pts(hi[0], hi[1], min_dist=cfg["hl_grid_min_dist"])
        lo_k = thin_pts(lo[0], lo[1], min_dist=cfg["hl_grid_min_dist"])

        hi_final = further_thin_latlon(hi[0][hi_k], hi[1][hi_k], lat_idx, lon_idx, lats, lon_plot, Z,
                                       min_deg=cfg["hl_deg_min_dist"])
        lo_final = further_thin_latlon(lo[0][lo_k], lo[1][lo_k], lat_idx, lon_idx, lats, lon_plot, Z,
                                       min_deg=cfg["hl_deg_min_dist"])

        for iy_s, ix_s in hi_final:
            iy = lat_idx[iy_s]; ix = lon_idx[ix_s]
            draw_HL(ax, float(lon_plot[ix]), float(lats[iy]), "H", float(Z[iy, ix]),
                    pc, lon_min, lon_max, lat_min, lat_max, cfg)
        for iy_s, ix_s in lo_final:
            iy = lat_idx[iy_s]; ix = lon_idx[ix_s]
            draw_HL(ax, float(lon_plot[ix]), float(lats[iy]), "L", float(Z[iy, ix]),
                    pc, lon_min, lon_max, lat_min, lat_max, cfg)

    if cfg["show_vort_symbols"]:
        winv = cfg["vort_window"]
        vmax = maximum_filter(V_sub, size=winv)
        vmin = minimum_filter(V_sub, size=winv)

        is_pos = (V_sub == vmax) & (V_sub > cfg["vort_threshold"])
        is_neg = (V_sub == vmin) & (V_sub < -cfg["vort_threshold"])

        pos = np.where(is_pos)
        neg = np.where(is_neg)

        pos_k = thin_pts(pos[0], pos[1], min_dist=cfg["vort_grid_min_dist"])
        neg_k = thin_pts(neg[0], neg[1], min_dist=cfg["vort_grid_min_dist"])

        pos_final = further_thin_vort(pos[0][pos_k], pos[1][pos_k], lat_idx, lon_idx, lats, lon_plot, V_sub,
                                      min_deg=cfg["vort_deg_min_dist"], positive=True)
        neg_final = further_thin_vort(neg[0][neg_k], neg[1][neg_k], lat_idx, lon_idx, lats, lon_plot, V_sub,
                                      min_deg=cfg["vort_deg_min_dist"], positive=True)

        for iy_s, ix_s in pos_final:
            iy = lat_idx[iy_s]; ix = lon_idx[ix_s]
            draw_vort_symbol(ax, float(lon_plot[ix]), float(lats[iy]), "+", float(V[iy, ix]),
                             pc, lon_min, lon_max, lat_min, lat_max, cfg)
        for iy_s, ix_s in neg_final:
            iy = lat_idx[iy_s]; ix = lon_idx[ix_s]
            draw_vort_symbol(ax, float(lon_plot[ix]), float(lats[iy]), "–", float(V[iy, ix]),
                             pc, lon_min, lon_max, lat_min, lat_max, cfg)


    # Save only if standalone
    if standalone:
        outpath = OUTDIR / cfg["output_filename"]
       # fig.tight_layout()
        fig.savefig(outpath, dpi=cfg["dpi"])
        print("Saved:", outpath)

    return ax


if __name__ == "__main__":
    plot_500hpa()
