# -*- coding: utf-8 -*-
"""
GDPS MSLP + 1000–500 hPa Thickness (dam) with ECCC-style H/L symbols
and boxed MSLP labels, configured via PLOT_CONFIG.
"""

import os
from copy import deepcopy
from pathlib import Path

import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib as mpl
import matplotlib.patheffects as PathEffects
import matplotlib.transforms as mtransforms

import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.feature import NaturalEarthFeature, ShapelyFeature

from scipy.ndimage import maximum_filter, minimum_filter
import geopandas as gpd


# --------------------------------------------------
# Helper functions
# --------------------------------------------------
def open_ds(grib_path: Path, indexname: str) -> xr.Dataset:
    """Open GRIB with cfgrib + index file."""
    return xr.open_dataset(
        grib_path,
        engine="cfgrib",
        backend_kwargs={"indexpath": indexname},
    )


def get_project_root() -> Path:
    """
    Returns the project root folder.
    Works in Jupyter (no __file__) and scripts (__file__ exists).
    """
    if "__file__" in globals():          # script mode
        return Path(__file__).resolve().parents[1]

    # Jupyter / interactive mode
    cwd = Path(os.getcwd()).resolve()
    if cwd.name == "src":
        return cwd.parent
    return cwd


def thin_pts(iy, ix, min_dist=8):
    """Simple thinning in grid space."""
    kept = []
    for j in range(len(iy)):
        y, x = iy[j], ix[j]
        if all((y - iy[k])**2 + (x - ix[k])**2 >= min_dist**2 for k in kept):
            kept.append(j)
    return kept


def further_thin_latlon(iy_sub, ix_sub, lat_idx, lon_idx,
                        lats_1d, lon_plot, Z, min_deg=1.5):
    """
    Extra thinning in lat/lon space for H/L centres.
    Keeps strongest systems first.
    """
    pts = []
    for iy_s, ix_s in zip(iy_sub, ix_sub):
        iy_global = lat_idx[iy_s]
        ix_global = lon_idx[ix_s]
        lat = float(lats_1d[iy_global])
        lon = float(lon_plot[ix_global])
        val = float(Z[iy_global, ix_global])
        pts.append((val, iy_s, ix_s, lat, lon))

    # strongest / deepest first
    pts.sort(reverse=True, key=lambda x: x[0])

    kept = []
    kept_latlon = []
    for val, iy_s, ix_s, lat, lon in pts:
        too_close = False
        for klat, klon in kept_latlon:
            dlat = lat - klat
            dlon = (lon - klon) * np.cos(np.radians((lat + klat) / 2.0))
            if (dlat*dlat + dlon*dlon) < min_deg * min_deg:
                too_close = True
                break
        if not too_close:
            kept.append((iy_s, ix_s))
            kept_latlon.append((lat, lon))
    return kept


def draw_HL(ax, lon, lat, letter, val, pc,
            lon_min, lon_max, lat_min, lat_max,
            cfg):
    """
    ECCC-style high/low symbol, but ONLY if the whole
    label stack fits inside the map extent.
    """
    d_letter = cfg["hl_d_letter"]
    d_value = cfg["hl_d_value"]
    pad_lon = cfg["hl_pad_lon"]
    pad_lat = cfg["hl_pad_lat"]

    lat_letter = lat + d_letter
    lat_center = lat
    lat_value = lat - d_value

    if (
        (lon < lon_min + pad_lon) or (lon > lon_max - pad_lon) or
        (lat_letter > lat_max - pad_lat) or
        (lat_value < lat_min + pad_lat)
    ):
        return

    # 1. Letter (H or L) with white halo
    txt = ax.text(
        lon, lat_letter, letter,
        transform=pc,
        ha="center", va="center",
        fontsize=cfg["hl_letter_fontsize"],
        fontweight="bold",
        color="black", zorder=12,
    )
    txt.set_path_effects([
        PathEffects.Stroke(linewidth=cfg["hl_letter_halo_width"],
                           foreground="white"),
        PathEffects.Normal()
    ])

    # 2. Circle with X
    circ = ax.text(
        lon, lat_center, "⊗",
        transform=pc,
        ha="center", va="center",
        fontsize=cfg["hl_center_fontsize"],
        color="black", zorder=12,
    )
    circ.set_path_effects([
        PathEffects.Stroke(linewidth=cfg["hl_center_halo_width"],
                           foreground="white"),
        PathEffects.Normal()
    ])

    # 3. Pressure number
    num = ax.text(
        lon, lat_value, f"{int(val)}",
        transform=pc,
        ha="center", va="center",
        fontsize=cfg["hl_value_fontsize"],
        fontweight="bold",
        color="black", zorder=12,
    )
    num.set_path_effects([
        PathEffects.Stroke(linewidth=cfg["hl_value_halo_width"],
                           foreground="white"),
        PathEffects.Normal()
    ])


# --------------------------------------------------
# Default configuration
# --------------------------------------------------
PLOT_CONFIG = {
    # --- Input files (relative to project root) ---
    "mslp_grib": "data/20251119T12Z_MSC_GDPS_Pressure_MSL_LatLon0.15_PT000H.grib2",
    "mslp_index": "mslp.idx",
    "thk_grib": "data/20251119T12Z_MSC_GDPS_Thickness_IsbL-1000to0500_LatLon0.15_PT000H.grib2",
    "thk_index": "thk1000_500.idx",
    "fire_outline": "fire_centers_all.geojson",

    # --- Projection / domain ---
    "central_longitude": -130.0,
    "central_latitude": 50.0,
    "extent": [-170.0, -100.0, 35.0, 75.0],  # [lon_min, lon_max, lat_min, lat_max]

    # --- Figure & margins ---
    "figsize": (10, 7),
    "dpi": 300,
    "tight_layout_pad": 0.2,
    "subplots_adjust": {"left": 0.03, "right": 0.97, "bottom": 0.03, "top": 0.93},

    # --- Gridlines & labels ---
    "grid_dx": 5,
    "grid_dy": 5,
    "lon_label_value": -140.0,
    "lat_label_value": 40.0,
    "label_fontsize": 7,
    "label_alpha": 0.65,

    # --- Base features ---
    "show_fire_boundary": True,
    "fire_edgecolor": "0.3",
    "fire_facecolor": "none",
    "fire_linewidth": 0.4,

    # --- MSLP contour settings ---
    "mslp_levels": list(np.arange(960, 1050, 4)),
    "mslp_linewidth": 1.0,
    "mslp_highlight_levels": [1000, 1024],
    "mslp_highlight_linewidth": 2.0,
    "mslp_label_lon": -140.0,
    "mslp_label_tol": 3.0,
    "mslp_label_min_lat_sep": 0.7,
    "mslp_label_fontsize": 6,

    # --- Thickness contour + shading settings ---
    "thk_levels": list(np.arange(480, 600, 6)),
    "thk_linewidth": 1.0,
    "thk_linestyle": "dashed",
    "shade_band": True,
    "shade_min": 534,
    "shade_max": 540,
    "shade_hatch": ".....",
    "shade_hatch_linewidth": 0.15,
    "thk_label_lon": -110.0,
    "thk_label_tol": 3.0,
    "thk_label_min_lat_sep": 0.7,
    "thk_label_fontsize": 6,

    # --- H/L detection ---
    "hl_window": 57,
    "hl_grid_min_dist": 8,
    "hl_deg_min_dist": 1.5,
    "show_HL": True,

    # --- H/L drawing style ---
    "hl_d_letter": 1.5,
    "hl_d_value": 1.2,
    "hl_pad_lon": 1.0,
    "hl_pad_lat": 1.0,
    "hl_letter_fontsize": 20,
    "hl_letter_halo_width": 3.0,
    "hl_center_fontsize": 10,
    "hl_center_halo_width": 2.0,
    "hl_value_fontsize": 8,
    "hl_value_halo_width": 2.0,

    # --- Title & output ---
    "title": "GDPS MSLP + 1000–500 hPa Thickness (dam)",
    "output_filename": "GDPS_small_domain_ECCCstyle.png",
}


# --------------------------------------------------
# Main plotting function
# --------------------------------------------------
def plot_mslp_thickness(cfg: dict | None = None):
    """
    Plot GDPS MSLP + 1000–500 hPa Thickness using settings from cfg.
    If cfg is None, uses PLOT_CONFIG.
    """
    # Merge defaults + user overrides
    config = deepcopy(PLOT_CONFIG)
    if cfg is not None:
        config.update(cfg)

    ROOT = get_project_root()
    OUTPUT_DIR = ROOT / "outputs"
    OUTPUT_DIR.mkdir(exist_ok=True)

    # --------------- Unpack config ---------------
    mslp_grib = ROOT / config["mslp_grib"]
    thk_grib = ROOT / config["thk_grib"]
    mslp_index = config["mslp_index"]
    thk_index = config["thk_index"]
    fire_outline_path = ROOT / config["fire_outline"]

    lon_min, lon_max, lat_min, lat_max = config["extent"]

    # --------------- Open datasets ---------------
    ds_msl = open_ds(mslp_grib, mslp_index)
    ds_thk = open_ds(thk_grib, thk_index)

    msl_var = list(ds_msl.data_vars)[0]
    thk_var = list(ds_thk.data_vars)[0]

    msl_raw = ds_msl[msl_var].squeeze(drop=True)   # Pa
    thk_raw = ds_thk[thk_var].squeeze(drop=True)   # gpm or dam

    mslp = msl_raw / 100.0  # Pa -> hPa

    thk_vals = thk_raw.values
    if thk_vals.max() > 1000:
        thickness = thk_raw / 10.0  # gpm -> dam
    else:
        thickness = thk_raw

    # Coordinates
    lats_1d = ds_msl["latitude"].values
    lons_1d = ds_msl["longitude"].values

    lon_wrapped = ((lons_1d + 180.0) % 360.0) - 180.0
    order = np.argsort(lon_wrapped)
    lon_plot = lon_wrapped[order]

    Z_full = mslp.values
    T_full = thickness.values

    Z = Z_full[:, order]
    T = T_full[:, order]

    fire_gdf = gpd.read_file(fire_outline_path)

    # --------------- Plot setup ---------------
    proj = ccrs.LambertConformal(
        central_longitude=config["central_longitude"],
        central_latitude=config["central_latitude"]
    )
    pc = ccrs.PlateCarree()

    plt.rcParams["font.size"] = 7
    plt.rcParams["axes.linewidth"] = 0.3

    fig = plt.figure(figsize=config["figsize"])
    ax = plt.axes(projection=proj)
    ax.set_extent(config["extent"], crs=pc)

    # Gridlines
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
    lat_label_value = config["lat_label_value"]
    lon_label_y_pos = lat_max - 1.5
    lat_label_x_pos = lon_min + 1.5

    label_style = dict(
        fontsize=config["label_fontsize"],
        color="black",
        alpha=config["label_alpha"],
        ha="center",
        va="center",
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

    # Base map
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

    if config["show_fire_boundary"]:
        fire_feature = ShapelyFeature(fire_gdf.geometry, crs=pc)
        ax.add_feature(
            fire_feature,
            edgecolor=config["fire_edgecolor"],
            facecolor=config["fire_facecolor"],
            linewidth=config["fire_linewidth"],
            zorder=1
        )

    # --------------- 4. MSLP contours ---------------
    msl_levels = np.array(config["mslp_levels"])
    cs_msl = ax.contour(
        lon_plot, lats_1d, Z,
        levels=msl_levels,
        colors="black",
        linewidths=config["mslp_linewidth"],
        transform=pc
    )

    # highlighted MSL levels
    highlight_msl = np.array(config["mslp_highlight_levels"])
    if highlight_msl.size > 0:
        ax.contour(
            lon_plot, lats_1d, Z,
            levels=highlight_msl,
            colors="black",
            linewidths=config["mslp_highlight_linewidth"],
            transform=pc
        )

    # boxed labels for all MSLP levels along one longitude
    label_lon = config["mslp_label_lon"]
    idx_lon = np.argmin(np.abs(lon_plot - label_lon))

    lat_mask = (lats_1d >= lat_min) & (lats_1d <= lat_max)
    lats_sub = lats_1d[lat_mask]
    Z_col_full = Z[:, idx_lon]
    Z_col = Z_col_full[lat_mask]

    tol_hpa = config["mslp_label_tol"]
    used_lats = []

    for lev in msl_levels:
        if Z_col.size == 0:
            continue

        iy_rel = int(np.argmin(np.abs(Z_col - lev)))
        diff = float(np.abs(Z_col[iy_rel] - lev))
        if diff > tol_hpa:
            continue

        lat_lab = float(lats_sub[iy_rel])
        if any(abs(lat_lab - ul) < config["mslp_label_min_lat_sep"] for ul in used_lats):
            continue
        used_lats.append(lat_lab)

        ax.text(
            label_lon, lat_lab, f"{int(lev)}",
            transform=pc,
            ha="center", va="center",
            fontsize=config["mslp_label_fontsize"],
            color="white",
            bbox=dict(
                boxstyle="square,pad=0.1",
                facecolor="black",
                edgecolor="black",
                linewidth=0.7
            ),
            zorder=8
        )

    # --------------- 5. Thickness contours + shaded band ---------------
    all_thk = np.array(config["thk_levels"])

    # temporarily change hatch linewidth
    old_hlw = mpl.rcParams.get("hatch.linewidth", 1.0)
    if config["shade_band"]:
        mpl.rcParams["hatch.linewidth"] = config["shade_hatch_linewidth"]
        band_min = config["shade_min"]
        band_max = config["shade_max"]

        cs_band = ax.contourf(
            lon_plot, lats_1d, T,
            levels=[band_min, band_max],
            colors="none",
            hatches=[config["shade_hatch"]],
            transform=pc,
            zorder=6
        )

        # style hatch outlines (Cartopy-safe)
        try:
            for coll in cs_band.legend_elements()[0]:
                try:
                    coll.set_edgecolor("black")
                    coll.set_linewidth(0.3)
                except Exception:
                    pass
        except Exception:
            pass

    # restore hatch linewidth
    mpl.rcParams["hatch.linewidth"] = old_hlw

    # Thickness contours
    cs_thk = ax.contour(
        lon_plot, lats_1d, T,
        levels=all_thk,
        colors="black",
        linewidths=config["thk_linewidth"],
        linestyles=config["thk_linestyle"],
        transform=pc,
        zorder=7
    )

    # Boxed thickness labels along lon = thk_label_lon
    thk_label_levels = all_thk
    label_lon_thk = config["thk_label_lon"]
    idx_lon_thk = np.argmin(np.abs(lon_plot - label_lon_thk))

    lat_mask_thk = (lats_1d >= lat_min) & (lats_1d <= lat_max)
    lats_sub_thk = lats_1d[lat_mask_thk]
    T_col_full = T[:, idx_lon_thk]
    T_col = T_col_full[lat_mask_thk]

    tol_dam = config["thk_label_tol"]
    used_lats_thk = []

    for lev in thk_label_levels:
        if T_col.size == 0:
            continue

        iy_rel = int(np.argmin(np.abs(T_col - lev)))
        diff = float(np.abs(T_col[iy_rel] - lev))
        if diff > tol_dam:
            continue

        lat_lab = float(lats_sub_thk[iy_rel])
        if any(abs(lat_lab - ul) < config["thk_label_min_lat_sep"]
               for ul in used_lats_thk):
            continue
        used_lats_thk.append(lat_lab)

        ax.text(
            label_lon_thk, lat_lab, f"{int(lev)}",
            transform=pc,
            ha="center", va="center",
            fontsize=config["thk_label_fontsize"],
            color="black",
            bbox=dict(
                boxstyle="square,pad=0.1",
                facecolor="none",
                edgecolor="black",
                linewidth=0.5
            ),
            zorder=8
        )

    # --------------- 6. High / Low centres ---------------
    if config["show_HL"]:
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

        hi_k = thin_pts(sub_hi[0], sub_hi[1],
                        min_dist=config["hl_grid_min_dist"])
        lo_k = thin_pts(sub_lo[0], sub_lo[1],
                        min_dist=config["hl_grid_min_dist"])

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
                lon_min, lon_max, lat_min, lat_max,
                config
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
                lon_min, lon_max, lat_min, lat_max,
                config
            )

    # --------------- 7. Title & save ---------------
    ax.set_title(config["title"], fontsize=10)

    # shrink margins
    fig.tight_layout(pad=config["tight_layout_pad"])
    plt.subplots_adjust(**config["subplots_adjust"])

    out_path = OUTPUT_DIR / config["output_filename"]
    plt.savefig(out_path, dpi=config["dpi"])
    plt.show()
    print(f"Saved: {out_path}")
