# -*- coding: utf-8 -*-
"""
GDPS 500 hPa Geopotential Height (dam) + Relative Vorticity

Styled to match the MSLP + thickness chart:
- Same projection, extent, BCWS boundary, gridlines
- Highlight 528, 546, 570 dam with thicker lines
- Relative vorticity as thin contours
- ECCC-style H/L symbols based on 500-hPa height
- Simple "control panel" via PLOT_CONFIG dict
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
import matplotlib.lines as mlines

# --------------------------------------------------
# Helper: project root (works in script & Jupyter)
# --------------------------------------------------
def get_project_root():
    """
    Returns the project root folder.
    Works in Jupyter (no __file__) and scripts (__file__ exists).
    """
    # Script mode (__file__ exists)
    if "__file__" in globals():
        return Path(__file__).resolve().parents[1]

    # Jupyter mode: start from current working directory
    cwd = Path(os.getcwd()).resolve()

    # If running inside /src, return its parent
    if cwd.name == "src":
        return cwd.parent

    # Otherwise assume cwd IS the project root
    return cwd

ROOT = get_project_root()
print("ROOT =", ROOT)
OUTPUT_DIR = ROOT / "outputs"


def add_eccc_banner(fig, cfg):
    """
    Draw an ECCC-style banner at the top of the figure, including:
      - top + middle forecast lines
      - 500 hPa / HEIGHT-HAUTEUR / VORTICITY-TOURBILLON band
      - left panel ('REGIONAL' / 'GEM')
      - legend row with field descriptions
    All coordinates are in figure space (0–1).
    """

    # --- Text from config ---
    top    = cfg.get("banner_top",   "")
    mid    = cfg.get("banner_mid",   "")
    left   = cfg.get("banner_left",  "")
    centre = cfg.get("banner_center","")
    right  = cfg.get("banner_right", "")

    panel_top    = cfg.get("panel_left_top",    "")
    panel_bottom = cfg.get("panel_left_bottom", "")

    leg_left   = cfg.get("legend_left",   "")
    leg_centre = cfg.get("legend_center", "")
    leg_right  = cfg.get("legend_right",  "")

    # --- Layout (tweak if you want) ---
    x0_panel = 0.02    # left edge of left panel
    x1_panel = 0.18    # right edge of left panel
    x2_full  = 0.98    # right edge of main band

    y4 = 0.99          # very top
    y3 = 0.965         # between top & mid
    y2 = 0.93          # bottom of mid line / top of main band
    y1 = 0.895         # bottom of main band / top of legend
    y0 = 0.865         # bottom of legend

    # -------------------------------------------------
    # 1) Top two forecast lines (centered)
    # -------------------------------------------------
    fig.text(0.5, 0.975, top,
             ha="center", va="top",
             fontsize=9, fontweight="bold")

    fig.text(0.5, 0.947, mid,
             ha="center", va="center",
             fontsize=8)

    # -------------------------------------------------
    # 2) 500 hPa / HEIGHT / VORTICITY band (row 3)
    # -------------------------------------------------
    fig.text(0.30, (y2+y1)/2.0, left,
             ha="center", va="center",
             fontsize=8, fontweight="bold")

    fig.text(0.50, (y2+y1)/2.0, centre,
             ha="center", va="center",
             fontsize=8, fontweight="bold")

    fig.text(0.80, (y2+y1)/2.0, right,
             ha="center", va="center",
             fontsize=8, fontweight="bold")

    # -------------------------------------------------
    # 3) Left panel: REGIONAL / GEM
    # -------------------------------------------------
    fig.text((x0_panel+x1_panel)/2.0, (y4+y3)/2.0, panel_top,
             ha="center", va="center",
             fontsize=10, fontweight="bold")

    fig.text((x0_panel+x1_panel)/2.0, (y2+y1)/2.0, panel_bottom,
             ha="center", va="center",
             fontsize=9, fontweight="bold")

    # Panel box
    for y_a, y_b in ((y4, y3), (y3, y1)):   # top box + bottom box
        for (xa, xb) in ((x0_panel, x1_panel),):
            # horizontal lines
            fig.add_artist(mlines.Line2D([xa, xb], [y_a, y_a],
                                        transform=fig.transFigure,
                                        color="black", linewidth=0.8))
            fig.add_artist(mlines.Line2D([xa, xb], [y_b, y_b],
                                        transform=fig.transFigure,
                                        color="black", linewidth=0.8))
            # vertical lines
            fig.add_artist(mlines.Line2D([xa, xa], [y_a, y_b],
                                        transform=fig.transFigure,
                                        color="black", linewidth=0.8))
            fig.add_artist(mlines.Line2D([xb, xb], [y_a, y_b],
                                        transform=fig.transFigure,
                                        color="black", linewidth=0.8))

    # -------------------------------------------------
    # 4) Legend row at bottom of header
    # -------------------------------------------------
    fig.text(0.20, (y1+y0)/2.0, leg_left,
             ha="left", va="center", fontsize=7)
    fig.text(0.50, (y1+y0)/2.0, leg_centre,
             ha="center", va="center", fontsize=7)
    fig.text(0.95, (y1+y0)/2.0, leg_right,
             ha="right", va="center", fontsize=7)

    # -------------------------------------------------
    # 5) Horizontal lines for band + legend + outer frame
    # -------------------------------------------------
    for y in (y4, y3, y2, y1, y0):
        fig.add_artist(mlines.Line2D([x0_panel, x2_full], [y, y],
                                    transform=fig.transFigure,
                                    color="black", linewidth=0.8))

    # vertical line separating left panel from main band
    fig.add_artist(mlines.Line2D([x1_panel, x1_panel], [y0, y4],
                                transform=fig.transFigure,
                                color="black", linewidth=0.8))


# --------------------------------------------------
# "Control panel" – edit here
# --------------------------------------------------
PLOT_CONFIG = {
    # --- Input files (relative to project root) ---
    "z500_grib": "data/20251121T12Z_MSC_GDPS_GeopotentialHeight_IsbL-0500_LatLon0.15_PT000H.grib2",
    "z500_index": "z500.idx",
    "vort_grib": "data/20251121T12Z_MSC_GDPS_RelativeVorticity_IsbL-0500_LatLon0.15_PT000H.grib2",
    "vort_index": "rv500.idx",
    "fire_outline": "fire_centers_all.geojson",

    # --- Map projection / domain ---
    "projection": "lambert",          # for future extension
    "central_longitude": -130.0,
    "central_latitude": 50.0,
    "extent": [-170.0, -100.0, 30.0, 75.0],  # [lon_min, lon_max, lat_min, lat_max]
    # --- Figure & margins ---
    "figsize": (10, 7),
    "dpi": 300,
    "tight_layout_pad": 0.2,
    "subplots_adjust": {"left": 0.03, "right": 0.97, "bottom": 0.03, "top": 0.93},
    
    # --- Gridlines & labels ---
    "grid_dx": 5,      # gridline spacing in deg
    "grid_dy": 5,
    "lon_label_value": -140.0,  # only one longitude label drawn
    "lat_label_value": 40.0,    # only one latitude label drawn,

    # --- 500 hPa height settings ---
    "height_interval": 6,                 # 6 dam spacing
    "height_range": [480, 600],           # min, max dam
    "height_highlight": [528, 546, 570],  # bold contours
    "height_label_lon": -140.0,           # ECCC-style boxed labels along this lon
    "height_label_tol": 3.0,              # how close (dam) the column must be

    # --- Relative vorticity settings (1e-5 s^-1) ---
    # Example: [-16, -8, 0, 8, 16]
    "vort_levels": list(np.arange(-16, 16, 8)),
    "vort_linewidth": 0.5,
    "vort_linestyle": "dashed",
    "vort_threshold": 0.0,      # threshold for + / − centres (1e-5 s^-1)
    "vort_window": 39,          # neighbourhood size for extrema
    "vort_grid_min_dist": 6,    # gridpoints for first thinning
    "vort_deg_min_dist": 1.0,   # degrees for second thinning

    # --- High / Low detection (500 hPa) ---
    "hl_window": 51,            # neighbourhood size for extrema
    "hl_grid_min_dist": 8,      # gridpoints for first thinning
    "hl_deg_min_dist": 1.5,     # degrees for second thinning

    # --- Visibility toggles ---
    "show_fire_boundary": False,
    "show_HL": True,
    "show_vort_symbols": True,

    # --- Output ---
    "output_filename": "GDPS_500hPa_Height_Vorticity_ECCCstyle.png",
    "dpi": 300,
    
}


# --------------------------------------------------
# Open GRIB helper
# --------------------------------------------------
def open_ds(grib_path: Path, indexname: str) -> xr.Dataset:
    return xr.open_dataset(
        grib_path,
        engine="cfgrib",
        backend_kwargs={"indexpath": indexname},
    )


# --------------------------------------------------
# Thinning utilities
# --------------------------------------------------
def thin_pts(iy, ix, min_dist=8):
    """Thin indices in grid space."""
    kept = []
    for j in range(len(iy)):
        y, x = iy[j], ix[j]
        if all((y - iy[k]) ** 2 + (x - ix[k]) ** 2 >= min_dist**2 for k in kept):
            kept.append(j)
    return kept


def further_thin_latlon(iy_sub, ix_sub, lat_idx, lon_idx,
                        lats_1d, lon_plot, Z, min_deg=1.5):
    """
    Additional thinning in lat/lon space for H/L.
    Always keeps strongest/highest system first.
    """
    pts = []
    for iy_s, ix_s in zip(iy_sub, ix_sub):
        iy_global = lat_idx[iy_s]
        ix_global = lon_idx[ix_s]
        lat = float(lats_1d[iy_global])
        lon = float(lon_plot[ix_global])
        val = float(Z[iy_global, ix_global])
        pts.append((val, iy_s, ix_s, lat, lon))

    # strongest/highest first
    pts.sort(reverse=True, key=lambda x: x[0])

    kept = []
    kept_latlon = []
    for val, iy_s, ix_s, lat, lon in pts:
        too_close = False
        for klat, klon in kept_latlon:
            dlat = lat - klat
            dlon = (lon - klon) * np.cos(np.radians((lat + klat) / 2.0))
            if (dlat * dlat + dlon * dlon) < min_deg**2:
                too_close = True
                break
        if not too_close:
            kept.append((iy_s, ix_s))
            kept_latlon.append((lat, lon))
    return kept


def further_thin_vort(iy_sub, ix_sub, lat_idx, lon_idx,
                      lats_1d, lon_plot, V_field,
                      min_deg=1.0, positive=True):
    """
    Additional thinning in lat/lon space for vorticity centres.
    Sorts by magnitude (strongest first).
    """
    pts = []
    for iy_s, ix_s in zip(iy_sub, ix_sub):
        iy_g = lat_idx[iy_s]
        ix_g = lon_idx[ix_s]
        lat = float(lats_1d[iy_g])
        lon = float(lon_plot[ix_g])
        val = float(V_field[iy_s, ix_s])
        pts.append((val, iy_s, ix_s, lat, lon))

    # sort: largest positive or most negative first
    if positive:
        pts.sort(reverse=True, key=lambda x: x[0])
    else:
        pts.sort(key=lambda x: x[0])  # most negative first

    kept = []
    kept_latlon = []
    for val, iy_s, ix_s, lat, lon in pts:
        too_close = False
        for klat, klon in kept_latlon:
            dlat = lat - klat
            dlon = (lon - klon) * np.cos(np.radians((lat + klat) / 2.0))
            if (dlat * dlat + dlon * dlon) < min_deg**2:
                too_close = True
                break
        if not too_close:
            kept.append((iy_s, ix_s))
            kept_latlon.append((lat, lon))
    return kept


# --------------------------------------------------
# Drawing helpers (H/L and +/- vort symbols)
# --------------------------------------------------
def draw_HL(ax, lon, lat, letter, val, pc,
            lon_min, lon_max, lat_min, lat_max):
    """
    ECCC-style 500-hPa H/L symbol, with halo.
    Suppresses labels that would fall outside the map.
    """
    d_letter = 1.5   # deg above centre
    d_value = 1.2    # deg below centre

    lat_letter = lat + d_letter
    lat_center = lat
    lat_value = lat - d_value

    pad_lon = 1.0
    pad_lat = 1.0

    if (
        (lon < lon_min + pad_lon) or (lon > lon_max - pad_lon) or
        (lat_letter > lat_max - pad_lat) or
        (lat_value < lat_min + pad_lat)
    ):
        return

    txt = ax.text(
        lon, lat_letter, letter,
        transform=pc,
        ha="center", va="center",
        fontsize=22, fontweight="bold",
        color="black", zorder=12,
    )
    txt.set_path_effects([
        PathEffects.Stroke(linewidth=3, foreground="white"),
        PathEffects.Normal()
    ])

    circ = ax.text(
        lon, lat_center, "⊗",
        transform=pc,
        ha="center", va="center",
        fontsize=10, color="black", zorder=12,
    )
    circ.set_path_effects([
        PathEffects.Stroke(linewidth=2, foreground="white"),
        PathEffects.Normal()
    ])

    num = ax.text(
        lon, lat_value, f"{int(val)}",
        transform=pc,
        ha="center", va="center",
        fontsize=10, fontweight="bold",
        color="black", zorder=12,
    )
    num.set_path_effects([
        PathEffects.Stroke(linewidth=2, foreground="white"),
        PathEffects.Normal()
    ])


def draw_vort_symbol(ax, lon, lat, sign, value, pc,
                     lon_min, lon_max, lat_min, lat_max):
    """
    Draw '+ / −' with the ECCC-style halo + numerical value below.
    """
    pad = 0.5
    if not (lon_min + pad <= lon <= lon_max - pad and
            lat_min + pad <= lat <= lat_max - pad):
        return

    txt = ax.text(
        lon, lat + 0.4, sign,
        transform=pc,
        ha="center", va="center",
        fontsize=5,
        color="black", zorder=10,
    )
    txt.set_path_effects([
        PathEffects.Stroke(linewidth=1.8, foreground="white"),
        PathEffects.Normal()
    ])

    val_txt = ax.text(
        lon, lat - 0.3, f"{int(abs(value))}",
        transform=pc,
        ha="center", va="center",
        fontsize=5,
        color="black", zorder=10,
    )
    val_txt.set_path_effects([
        PathEffects.Stroke(linewidth=1.5, foreground="white"),
        PathEffects.Normal()
    ])


# --------------------------------------------------
# Main plotting function
# --------------------------------------------------
def plot_500hpa(config: dict = None):
    """
    Main entry point to plot 500 hPa height + relative vorticity.
    All behaviour controlled by the config dictionary (PLOT_CONFIG).
    """
    if config is None:
        config = PLOT_CONFIG

    # --- Resolve paths ---
    f_z500 = ROOT / config["z500_grib"]
    f_vort = ROOT / config["vort_grib"]
    fire_outline_path = ROOT / config["fire_outline"]

    # --- Open data ---
    ds_z500 = open_ds(f_z500, config["z500_index"])
    ds_vort = open_ds(f_vort, config["vort_index"])

    z_var = list(ds_z500.data_vars)[0]
    v_var = list(ds_vort.data_vars)[0]

    z_raw = ds_z500[z_var].squeeze(drop=True)
    v_raw = ds_vort[v_var].squeeze(drop=True)

    # Geopotential height: convert to dam
    z_vals = z_raw.values
    if z_vals.max() > 1000:
        H500 = z_raw / 10.0
    else:
        H500 = z_raw

    # Relative vorticity: convert to 1e-5 s^-1
    V_raw = v_raw.values
    if np.nanmax(np.abs(V_raw)) < 1e-3:
        vort = v_raw * 1e5
        print("unit convert works")
    else:
        vort = v_raw * 1e5

    # Coordinates
    lats_1d = ds_z500["latitude"].values
    lons_1d = ds_z500["longitude"].values

    # Wrap longitude 0–360 -> -180–180 and reorder fields
    lon_wrapped = ((lons_1d + 180.0) % 360.0) - 180.0
    order = np.argsort(lon_wrapped)
    lon_plot = lon_wrapped[order]

    Z_full = H500.values
    V_full = vort.values

    Z = Z_full[:, order]
    V = V_full[:, order]

    # Fire centres
    try:
        fire_gdf = gpd.read_file(fire_outline_path)
    except Exception as e:
        fire_gdf = None
        print("Warning: could not read fire-centre boundary:", e)

    # --- Map settings ---
    lon_min, lon_max, lat_min, lat_max = config["extent"]
    extent = [lon_min, lon_max, lat_min, lat_max]

    proj = ccrs.LambertConformal(
        central_longitude=config["central_longitude"],
        central_latitude=config["central_latitude"]
    )
    pc = ccrs.PlateCarree()

    plt.rcParams["font.size"] = 7
    plt.rcParams["axes.linewidth"] = 0.3

    fig = plt.figure(figsize=config["figsize"])  #reviced on 2 Dec, set the ECCC banner
    ax = plt.axes(projection=proj)
    
    # fig = plt.figure(figsize=config["figsize"])

    # # left, bottom, width, height in figure coordinates
    # ax = fig.add_axes([0.06, 0.06, 0.88, 0.78], projection=proj)

    
    ax.set_extent(extent, crs=pc)

    # --------------------------------------------------
    # Gridlines + single lat/lon labels
    # --------------------------------------------------
    gl = ax.gridlines(
        crs=pc,
        draw_labels=False,
        linewidth=0.4,
        color="black",
        alpha=0.4,
        linestyle="dotted"
    )
    gl.xlocator = mticker.FixedLocator(
        np.arange(-180, 181, config["grid_dx"])
    )
    gl.ylocator = mticker.FixedLocator(
        np.arange(0, 91, config["grid_dy"])
    )

    lon_label_value = config["lon_label_value"]
    lon_label_y_pos = lat_max - 1.5

    lat_label_value = config["lat_label_value"]
    lat_label_x_pos = lon_min + 1.5

    label_style = dict(
        fontsize=7,
        color="black",
        alpha=0.65,
        ha="center",
        va="center"
    )

    ax.text(
        lon_label_value,
        lon_label_y_pos,
        f"{abs(lon_label_value)}W",
        transform=pc,
        **label_style
    )

    ax.text(
        lat_label_x_pos,
        lat_label_value,
        f"{lat_label_value}N",
        transform=pc,
        **label_style
    )

    # --------------------------------------------------
    # Base map features
    # --------------------------------------------------
    ax.add_feature(
        cfeature.LAND,
        edgecolor="black",
        facecolor="white",
        linewidth=0.4
    )
    ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
    ax.add_feature(cfeature.BORDERS, linewidth=0.4)

    provinces = NaturalEarthFeature(
        "cultural",
        "admin_1_states_provinces_lines",
        "50m",
        facecolor="none"
    )
    ax.add_feature(provinces, edgecolor="black", linewidth=0.5)

    if config["show_fire_boundary"] and fire_gdf is not None:
        fire_feature = ShapelyFeature(
            fire_gdf.geometry,
            crs=pc,
        )
        ax.add_feature(
            fire_feature,
            edgecolor="0.3",
            facecolor="none",
            linewidth=0.5,
            zorder=1
        )

    # --------------------------------------------------
    # 500-hPa HEIGHT contours (dam)
    # --------------------------------------------------
    h_min, h_max = config["height_range"]
    h_int = config["height_interval"]
    h_levels = np.arange(h_min, h_max, h_int)
    highlight_h = config["height_highlight"]

    cs_h = ax.contour(
        lon_plot, lats_1d, Z,
        levels=h_levels,
        colors="black",
        linewidths=1.0,
        transform=pc,
        zorder=5
    )

    ax.contour(
        lon_plot, lats_1d, Z,
        levels=highlight_h,
        colors="black",
        linewidths=2.0,
        transform=pc,
        zorder=6
    )

    # ECCC-style boxed height labels
    label_lon_h = config["height_label_lon"]
    idx_lon_h = np.argmin(np.abs(lon_plot - label_lon_h))

    lat_mask_h = (lats_1d >= lat_min) & (lats_1d <= lat_max)
    lats_sub_h = lats_1d[lat_mask_h]
    Z_col_full = Z[:, idx_lon_h]
    Z_col = Z_col_full[lat_mask_h]

    tol_dam = config["height_label_tol"]
    used_lats_h = []

    for lev in h_levels:
        if Z_col.size == 0:
            continue
        iy_rel = int(np.argmin(np.abs(Z_col - lev)))
        diff = float(np.abs(Z_col[iy_rel] - lev))
        if diff > tol_dam:
            continue

        lat_lab = float(lats_sub_h[iy_rel])
        if any(abs(lat_lab - ul) < 0.7 for ul in used_lats_h):
            continue
        used_lats_h.append(lat_lab)

        ax.text(
            label_lon_h, lat_lab, f"{int(lev)}",
            transform=pc,
            ha="center", va="center",
            fontsize=6,
            color="white",
            bbox=dict(
                boxstyle="square,pad=0.1",
                facecolor="black",
                edgecolor="black",
                linewidth=0.6
            ),
            zorder=8
        )

    # --------------------------------------------------
    # Relative vorticity contours (1e-5 s^-1)
    # --------------------------------------------------
    v_levels = np.array(config["vort_levels"])
    cs_v = ax.contour(
        lon_plot, lats_1d, V,
        levels=v_levels,
        colors="black",
        linewidths=config["vort_linewidth"],
        linestyles=config["vort_linestyle"],
        transform=pc,
        zorder=4
    )

    # --------------------------------------------------
    # 6. High / Low centres of 500-hPa HEIGHT
    # --------------------------------------------------
    lat_mask_full = (lats_1d >= lat_min) & (lats_1d <= lat_max)
    lon_mask_full = (lon_plot >= lon_min) & (lon_plot <= lon_max)

    lat_idx = np.where(lat_mask_full)[0]
    lon_idx = np.where(lon_mask_full)[0]

    Z_sub = Z[np.ix_(lat_idx, lon_idx)]

    win = config["hl_window"]
    zmax = maximum_filter(Z_sub, size=win)
    zmin = minimum_filter(Z_sub, size=win)

    is_high = (Z_sub == zmax)
    is_low = (Z_sub == zmin)

    sub_hi = np.where(is_high)
    sub_lo = np.where(is_low)

    hi_k = thin_pts(sub_hi[0], sub_hi[1], min_dist=config["hl_grid_min_dist"])
    lo_k = thin_pts(sub_lo[0], sub_lo[1], min_dist=config["hl_grid_min_dist"])

    hi_final = further_thin_latlon(
        sub_hi[0][hi_k], sub_hi[1][hi_k],
        lat_idx, lon_idx, lats_1d, lon_plot, Z,
        min_deg=config["hl_deg_min_dist"]
    )
    lo_final = further_thin_latlon(
        sub_lo[0][lo_k], sub_lo[1][lo_k],
        lat_idx, lon_idx, lats_1d, lon_plot, Z,
        min_deg=config["hl_deg_min_dist"]
    )

    if config["show_HL"]:
        for iy_s, ix_s in hi_final:
            iy = lat_idx[iy_s]
            ix = lon_idx[ix_s]
            draw_HL(
                ax,
                float(lon_plot[ix]),
                float(lats_1d[iy]),
                "H",
                float(Z[iy, ix]),
                pc,
                lon_min, lon_max, lat_min, lat_max
            )

        for iy_s, ix_s in lo_final:
            iy = lat_idx[iy_s]
            ix = lon_idx[ix_s]
            draw_HL(
                ax,
                float(lon_plot[ix]),
                float(lats_1d[iy]),
                "L",
                float(Z[iy, ix]),
                pc,
                lon_min, lon_max, lat_min, lat_max
            )

    # --------------------------------------------------
    # 6b. Vorticity '+' and '−' centres (sigma-style markers)
    # --------------------------------------------------
    if config["show_vort_symbols"]:
        V_sub = V[np.ix_(lat_idx, lon_idx)]

        win_v = config["vort_window"]
        vmax = maximum_filter(V_sub, size=win_v)
        vmin = minimum_filter(V_sub, size=win_v)

        is_pos = (V_sub == vmax)
        is_neg = (V_sub == vmin)

        vort_thresh = config["vort_threshold"]
        is_pos &= (V_sub > vort_thresh)
        is_neg &= (V_sub < -vort_thresh)

        pos_idx = np.where(is_pos)
        neg_idx = np.where(is_neg)

        pos_k = thin_pts(pos_idx[0], pos_idx[1],
                         min_dist=config["vort_grid_min_dist"])
        neg_k = thin_pts(neg_idx[0], neg_idx[1],
                         min_dist=config["vort_grid_min_dist"])

        pos_final = further_thin_vort(
            pos_idx[0][pos_k], pos_idx[1][pos_k],
            lat_idx, lon_idx, lats_1d, lon_plot, V_sub,
            min_deg=config["vort_deg_min_dist"],
            positive=True
        )
        neg_final = further_thin_vort(
            neg_idx[0][neg_k], neg_idx[1][neg_k],
            lat_idx, lon_idx, lats_1d, lon_plot, V_sub,
            min_deg=config["vort_deg_min_dist"],
            positive=False
        )

        for iy_s, ix_s in pos_final:
            iy = lat_idx[iy_s]
            ix = lon_idx[ix_s]
            vort_val = float(V[iy, ix])
            draw_vort_symbol(
                ax,
                float(lon_plot[ix]),
                float(lats_1d[iy]),
                "+",
                vort_val,
                pc,
                lon_min, lon_max, lat_min, lat_max
            )

        for iy_s, ix_s in neg_final:
            iy = lat_idx[iy_s]
            ix = lon_idx[ix_s]
            vort_val = float(V[iy, ix])
            draw_vort_symbol(
                ax,
                float(lon_plot[ix]),
                float(lats_1d[iy]),
                "–",
                vort_val,
                pc,
                lon_min, lon_max, lat_min, lat_max
            )

    # --------------------------------------------------
    # 7. Title & save
    # --------------------------------------------------
    if config.get("use_banner_header", False):
        add_eccc_banner(fig, config)
    else:
        ax.set_title("GDPS 500 hPa Height (dam) + Relative Vorticity (1e-5 s⁻¹)",
                 fontsize=10)

    out_path = OUTPUT_DIR / config["output_filename"]
    fig.tight_layout()
    # plt.subplots_adjust(
    # left=0.03,
    # right=0.97,
    # bottom=0.03,
    # top=0.93)

    fig.savefig(out_path, dpi=config["dpi"])
    
    print("Saved:", out_path)


# --------------------------------------------------
# Script entry point
# --------------------------------------------------
if __name__ == "__main__":
    plot_500hpa(PLOT_CONFIG)
