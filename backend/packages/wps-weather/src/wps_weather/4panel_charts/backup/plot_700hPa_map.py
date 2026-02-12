# -*- coding: utf-8 -*-
"""
GDPS 700 hPa Height + Layer-Mean Humidity (850–700–500)
ECCC-style:
- 700 hPa height contours (highlight 300 & 276 dam)
- Layer-mean RH from 850, 700, 500 hPa
- RH 50 / 70 / 90% contours + 70–90 & 90+ shaded with dots
- H/L centres based on 700-hPa height (same style as 500-hPa map)
"""

import os
from pathlib import Path
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.ticker as mticker
import matplotlib.patheffects as PathEffects

import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.feature import NaturalEarthFeature, ShapelyFeature
from scipy.ndimage import maximum_filter, minimum_filter
import geopandas as gpd


# --------------------------------------------------
# Helpers
# --------------------------------------------------
def open_ds(path: Path, indexname: str):
    """Open a GRIB file with cfgrib + explicit index file."""
    return xr.open_dataset(
        path,
        engine="cfgrib",
        backend_kwargs={"indexpath": indexname},
    )


def get_project_root():
    """Return project root (works in script and Jupyter)."""
    if "__file__" in globals():
        return Path(__file__).resolve().parents[1]

    cwd = Path(os.getcwd()).resolve()
    if cwd.name == "src":
        return cwd.parent
    return cwd


def thin_pts(iy, ix, min_dist=8):
    """First-pass thinning in grid space."""
    kept = []
    for j in range(len(iy)):
        y, x = iy[j], ix[j]
        if all((y - iy[k])**2 + (x - ix[k])**2 >= min_dist**2 for k in kept):
            kept.append(j)
    return kept


def further_thin_latlon(iy_sub, ix_sub, lat_idx, lon_idx,
                        lats_1d, lon_plot, Z, min_deg=1.5):
    """
    Second thinning in lat/lon space. Keeps strongest centres first.
    iy_sub, ix_sub are indices in the sub-grid.
    """
    pts = []
    for iy_s, ix_s in zip(iy_sub, ix_sub):
        iy_g = lat_idx[iy_s]
        ix_g = lon_idx[ix_s]
        lat = float(lats_1d[iy_g])
        lon = float(lon_plot[ix_g])
        val = float(Z[iy_g, ix_g])
        pts.append((val, iy_s, ix_s, lat, lon))

    # strongest highs / deepest lows first
    pts.sort(reverse=True, key=lambda x: x[0])

    kept = []
    kept_latlon = []
    for val, iy_s, ix_s, lat, lon in pts:
        too_close = False
        for klat, klon in kept_latlon:
            dlat = lat - klat
            dlon = (lon - klon) * np.cos(np.radians((lat + klat) / 2.0))
            if (dlat*dlat + dlon*dlon) < min_deg*min_deg:
                too_close = True
                break
        if not too_close:
            kept.append((iy_s, ix_s))
            kept_latlon.append((lat, lon))
    return kept


def draw_HL(ax, lon, lat, letter, val, pc,
            lon_min, lon_max, lat_min, lat_max,
            d_letter=1.5, d_value=1.2,
            letter_fs=22, value_fs=10):
    """
    Draw an ECCC-style H/L symbol with halo and value below.
    Suppresses labels that would fall outside the map extent.
    """
    lat_letter = lat + d_letter
    lat_value  = lat - d_value

    pad_lon = 1.0
    pad_lat = 1.0

    if (
        lon < lon_min + pad_lon or lon > lon_max - pad_lon or
        lat_letter > lat_max - pad_lat or
        lat_value  < lat_min + pad_lat
    ):
        return

    # H/L letter
    txt = ax.text(
        lon, lat_letter, letter,
        transform=pc,
        ha="center", va="center",
        fontsize=letter_fs, fontweight="bold",
        color="black", zorder=12,
    )
    txt.set_path_effects([
        PathEffects.Stroke(linewidth=3, foreground="white"),
        PathEffects.Normal()
    ])

    # Circle with X
    circ = ax.text(
        lon, lat, "⊗",
        transform=pc,
        ha="center", va="center",
        fontsize=10, color="black", zorder=12,
    )
    circ.set_path_effects([
        PathEffects.Stroke(linewidth=2, foreground="white"),
        PathEffects.Normal()
    ])

    # Value
    num = ax.text(
        lon, lat_value, f"{int(val)}",
        transform=pc,
        ha="center", va="center",
        fontsize=value_fs, fontweight="bold",
        color="black", zorder=12,
    )
    num.set_path_effects([
        PathEffects.Stroke(linewidth=2, foreground="white"),
        PathEffects.Normal()
    ])

def add_column_labels(ax, lon_plot, lats, field2d,
                      lon_label, lat_min, lat_max,
                      levels, tol, min_dlat,
                      pc, text_kwargs, bbox_kwargs):
    """
    ECCC-style column labels along a single longitude.

    field2d: 2D array (lat, lon)
    lon_label: longitude where labels are placed
    levels: list of values to label
    tol: max |field - level| to accept (same units as field)
    min_dlat: minimum separation between labels (degrees)
    """
    idx_lon = np.argmin(np.abs(lon_plot - lon_label))

    lat_mask = (lats >= lat_min) & (lats <= lat_max)
    lats_sub = lats[lat_mask]
    col_full = field2d[:, idx_lon]
    col = col_full[lat_mask]

    used_lats = []

    for lev in levels:
        if col.size == 0:
            continue

        iy_rel = int(np.argmin(np.abs(col - lev)))
        diff = float(abs(col[iy_rel] - lev))
        if diff > tol:
            continue

        lat_lab = float(lats_sub[iy_rel])
        if any(abs(lat_lab - ul) < min_dlat for ul in used_lats):
            continue
        used_lats.append(lat_lab)

        ax.text(
            lon_label, lat_lab, f"{int(lev)}",
            transform=pc,
            ha="center", va="center",
            bbox=bbox_kwargs,
            zorder=8,
            **text_kwargs,
        )

# --------------------------------------------------
# DEFAULT CONFIG
# --------------------------------------------------
PLOT_CONFIG_700 = {
    # =====  Height file  =====
    "z700_grib": "data/20251121T12Z_MSC_GDPS_GeopotentialHeight_IsbL-0700_LatLon0.15_PT000H.grib2",
    "z700_index": "z700.idx",

    # =====  Three Relative Humidity files  =====
    "rh850_grib": "data/20251121T12Z_MSC_GDPS_RelativeHumidity_IsbL-0850_LatLon0.15_PT000H.grib2",
    "rh850_index": "rh850.idx",

    "rh700_grib": "data/20251121T12Z_MSC_GDPS_RelativeHumidity_IsbL-0700_LatLon0.15_PT000H.grib2",
    "rh700_index": "rh700.idx",

    "rh500_grib": "data/20251121T12Z_MSC_GDPS_RelativeHumidity_IsbL-0500_LatLon0.15_PT000H.grib2",
    "rh500_index": "rh500.idx",

    # Fire boundary
    "fire_outline": "fire_centers_all.geojson",
    "show_fire_boundary": False,
    "fire_facecolor": "none",
    "fire_edgecolor": "0.3",
    "fire_linewidth": 1.0,

    # --- Domain / projection ---
    "central_longitude": -130.0,
    "central_latitude": 50.0,
    "extent": [-170.0, -100.0, 30.0, 75.0],

    # --- Gridlines ---
    "grid_dx": 5,
    "grid_dy": 5,
    "lon_label_value": -140.0,
    "lat_label_value": 40.0,

    # --- 700 hPa heights ---
    "height_interval": 6,
    "height_range": [240, 330],
    "height_highlight": [300, 276],
    "height_label_lon": -140.0,
    "height_label_tol": 3.0,
    "height_label_min_dlat": 0.7,

    # --- Humidity settings ---
    "rh_levels": [50, 70, 90],
    "rh_linewidth": 0.8,
    "rh_linestyle": "dashed",

    "shade_70_90": True,
    "shade_90_plus": True,
    "shade_70_90_hatch": ".....",
    "shade_90_plus_hatch": ".......",
    "shade_70_color": "#c6e8b5",
    "shade_90_color": "#a8d8f0",

    # --- High / Low detection on 700 hPa height ---
    "show_HL": True,
    "hl_window": 51,          # neighbourhood size for extrema
    "hl_grid_min_dist": 8,    # gridpoints for first thinning
    "hl_deg_min_dist": 1.5,   # degrees for second thinning
    "hl_d_letter": 1.5,
    "hl_d_value": 1.2,
    "hl_letter_fontsize": 22,
    "hl_value_fontsize": 10,

    # --- Styling ---
    "figsize": (10, 7),
    "dpi": 300,
    "title": "GDPS 700 hPa Height (dam) + Layer Humidity (850–700–500 hPa)",
    "base_fontsize": 7,
    "axes_linewidth": 0.3,

    # --- Output ---
    "output_dir": "outputs",
    "output_filename": "GDPS_700hPa_Height_Humidity_ECCCstyle.png",
}


# --------------------------------------------------
# MAIN PLOT FUNCTION
# --------------------------------------------------
def plot_700hpa(cfg: dict):
    ROOT = get_project_root()
    OUTPUT_DIR = ROOT / cfg["output_dir"]
    OUTPUT_DIR.mkdir(exist_ok=True)

    plt.rcParams["font.size"] = cfg.get("base_fontsize", 7)
    plt.rcParams["axes.linewidth"] = cfg.get("axes_linewidth", 0.3)

    pc = ccrs.PlateCarree()
    proj = ccrs.LambertConformal(
        central_longitude=cfg["central_longitude"],
        central_latitude=cfg["central_latitude"],
    )

    # --------------------------------------------------
    # 1. LOAD 700 HPA HEIGHT
    # --------------------------------------------------
    ds_z700 = open_ds(ROOT / cfg["z700_grib"], cfg["z700_index"])
    z_var = list(ds_z700.data_vars)[0]
    z700_raw = ds_z700[z_var].squeeze()

    # Convert m → dam if needed
    if float(z700_raw.max()) > 1000:
        H700 = z700_raw / 10.0
    else:
        H700 = z700_raw

    # --------------------------------------------------
    # 2. LOAD THREE RH FIELDS & COMPUTE LAYER MEAN
    # --------------------------------------------------
    ds_rh850 = open_ds(ROOT / cfg["rh850_grib"], cfg["rh850_index"])
    ds_rh700 = open_ds(ROOT / cfg["rh700_grib"], cfg["rh700_index"])
    ds_rh500 = open_ds(ROOT / cfg["rh500_grib"], cfg["rh500_index"])

    rh850 = list(ds_rh850.data_vars.values())[0].squeeze()
    rh700 = list(ds_rh700.data_vars.values())[0].squeeze()
    rh500 = list(ds_rh500.data_vars.values())[0].squeeze()

    RH = (rh850 + rh700 + rh500) / 3.0

    # --------------------------------------------------
    # 3. WRAP LONGITUDE 360→180
    # --------------------------------------------------
    lats = ds_z700["latitude"].values
    lons = ds_z700["longitude"].values

    lon_wrapped = ((lons + 180.0) % 360.0) - 180.0
    order = np.argsort(lon_wrapped)

    lon_plot = lon_wrapped[order]

    Z = H700.values[:, order]
    RH = RH.values[:, order]

    ny, nx = Z.shape

    # --------------------------------------------------
    # 4. FIGURE / AXES
    # --------------------------------------------------
    fig = plt.figure(figsize=cfg["figsize"])
    ax = plt.axes(projection=proj)

    lon_min, lon_max, lat_min, lat_max = cfg["extent"]
    ax.set_extent(cfg["extent"], crs=pc)

    # --------------------------------------------------
    # 5. GRIDLINES + SINGLE LABELS
    # --------------------------------------------------
    gl = ax.gridlines(
        draw_labels=False,
        crs=pc,
        color="black",
        linewidth=0.4,
        alpha=0.4,
        linestyle="dotted",
    )
    gl.xlocator = mticker.FixedLocator(np.arange(-180, 181, cfg["grid_dx"]))
    gl.ylocator = mticker.FixedLocator(np.arange(0, 91, cfg["grid_dy"]))

    ax.text(
        cfg["lon_label_value"], lat_max - 1.5,
        f"{abs(cfg['lon_label_value'])}W",
        transform=pc,
        fontsize=7, alpha=0.65,
        ha="center", va="center"
    )
    ax.text(
        lon_min + 1.5, cfg["lat_label_value"],
        f"{cfg['lat_label_value']}N",
        transform=pc,
        fontsize=7, alpha=0.65,
        ha="center", va="center"
    )

    # --------------------------------------------------
    # 6. BASE MAP FEATURES
    # --------------------------------------------------
    ax.add_feature(cfeature.LAND, facecolor="white", edgecolor="black", linewidth=0.4)
    ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
    ax.add_feature(cfeature.BORDERS, linewidth=0.4)

    provinces = NaturalEarthFeature(
        "cultural", "admin_1_states_provinces_lines", "50m", facecolor="none"
    )
    ax.add_feature(provinces, edgecolor="black", linewidth=0.5, zorder=10)

    # Optional fire boundary
    if cfg.get("show_fire_boundary", False):
        fire_gdf = gpd.read_file(ROOT / cfg["fire_outline"])
        fire_feature = ShapelyFeature(fire_gdf.geometry, crs=pc)
        ax.add_feature(
            fire_feature,
            facecolor=cfg.get("fire_facecolor", "none"),
            edgecolor=cfg.get("fire_edgecolor", "0.3"),
            linewidth=cfg.get("fire_linewidth", 1.0),
            zorder=7,
        )

    # --------------------------------------------------
    # 7. 700 HPA HEIGHT CONTOURS
    # --------------------------------------------------
    hmin, hmax = cfg["height_range"]
    hlev = np.arange(hmin, hmax + cfg["height_interval"], cfg["height_interval"])

    ax.contour(
        lon_plot, lats, Z,
        levels=hlev,
        colors="black",
        linewidths=1.0,
        transform=pc,
        zorder=5,
    )

    ax.contour(
        lon_plot, lats, Z,
        levels=cfg["height_highlight"],
        colors="black",
        linewidths=2.0,
        transform=pc,
        zorder=6,
    )
    # --- BLACK BOXED HEIGHT LABELS (264–318 dam) ---
    add_column_labels(
        ax,
        lon_plot,
        lats,
        Z,
        cfg["height_label_lon"],
        lat_min,
        lat_max,
        cfg["height_label_levels"],
        cfg["height_label_tol"],
        cfg["height_label_min_dlat"],
        pc,
        text_kwargs=dict(fontsize=6, color="white"),
        bbox_kwargs=dict(
            boxstyle="square,pad=0.1",
            facecolor="black",
            edgecolor="black",
            linewidth=0.7,
        ),
    )

    # --------------------------------------------------
    # 8. HUMIDITY SHADING + CONTOURS
    # --------------------------------------------------
    old_hlw = mpl.rcParams["hatch.linewidth"]
    mpl.rcParams["hatch.linewidth"] = 0.15

    if cfg["shade_70_90"]:
        ax.contourf(
            lon_plot, lats, RH,
            levels=[70, 90],
            colors=[cfg["shade_70_color"]],
            hatches=[cfg["shade_70_90_hatch"]],
            transform=pc,
            zorder=3,
        )

    if cfg["shade_90_plus"]:
        ax.contourf(
            lon_plot, lats, RH,
            levels=[90, 100],
            colors=[cfg["shade_90_color"]],
            hatches=[cfg["shade_90_plus_hatch"]],
            transform=pc,
            zorder=4,
        )

    mpl.rcParams["hatch.linewidth"] = old_hlw

    ax.contour(
        lon_plot, lats, RH,
        levels=cfg["rh_levels"],
        colors="black",
        linewidths=cfg["rh_linewidth"],
        linestyles=cfg["rh_linestyle"],
        transform=pc,
        zorder=4,
    )
    # --- WHITE BOXED RH LABELS (50/70/90) ---
    for lon_lab in cfg["rh_label_lons"]:
        add_column_labels(
            ax,
            lon_plot,
            lats,
            RH,
            lon_lab,
            lat_min,
            lat_max,
            cfg["rh_label_levels"],
            cfg["rh_label_tol"],
            cfg["rh_label_min_dlat"],
            pc,
            text_kwargs=dict(fontsize=6, color="black"),
            bbox_kwargs=dict(
                boxstyle="square,pad=0.1",
                facecolor="white",   # white box
                edgecolor="black",
                linewidth=0.7,
            ),
        )
    # --------------------------------------------------
    # 9. H/L CENTRES ON 700 HPA HEIGHT
    # --------------------------------------------------
    if cfg.get("show_HL", True):
        lat_mask_full = (lats >= lat_min) & (lats <= lat_max)
        lon_mask_full = (lon_plot >= lon_min) & (lon_plot <= lon_max)

        lat_idx = np.where(lat_mask_full)[0]
        lon_idx = np.where(lon_mask_full)[0]

        Z_sub = Z[np.ix_(lat_idx, lon_idx)]

        win = cfg["hl_window"]
        zmax = maximum_filter(Z_sub, size=win)
        zmin = minimum_filter(Z_sub, size=win)

        is_high = (Z_sub == zmax)
        is_low  = (Z_sub == zmin)

        sub_hi = np.where(is_high)
        sub_lo = np.where(is_low)

        hi_k = thin_pts(sub_hi[0], sub_hi[1], min_dist=cfg["hl_grid_min_dist"])
        lo_k = thin_pts(sub_lo[0], sub_lo[1], min_dist=cfg["hl_grid_min_dist"])

        hi_final = further_thin_latlon(
            sub_hi[0][hi_k], sub_hi[1][hi_k],
            lat_idx, lon_idx, lats, lon_plot, Z,
            min_deg=cfg["hl_deg_min_dist"],
        )
        lo_final = further_thin_latlon(
            sub_lo[0][lo_k], sub_lo[1][lo_k],
            lat_idx, lon_idx, lats, lon_plot, Z,
            min_deg=cfg["hl_deg_min_dist"],
        )

        for iy_s, ix_s in hi_final:
            iy = lat_idx[iy_s]
            ix = lon_idx[ix_s]
            draw_HL(
                ax,
                float(lon_plot[ix]),
                float(lats[iy]),
                "H",
                float(Z[iy, ix]),
                pc,
                lon_min, lon_max, lat_min, lat_max,
                d_letter=cfg["hl_d_letter"],
                d_value=cfg["hl_d_value"],
                letter_fs=cfg["hl_letter_fontsize"],
                value_fs=cfg["hl_value_fontsize"],
            )

        for iy_s, ix_s in lo_final:
            iy = lat_idx[iy_s]
            ix = lon_idx[ix_s]
            draw_HL(
                ax,
                float(lon_plot[ix]),
                float(lats[iy]),
                "L",
                float(Z[iy, ix]),
                pc,
                lon_min, lon_max, lat_min, lat_max,
                d_letter=cfg["hl_d_letter"],
                d_value=cfg["hl_d_value"],
                letter_fs=cfg["hl_letter_fontsize"],
                value_fs=cfg["hl_value_fontsize"],
            )

    # --------------------------------------------------
    # 10. TITLE / SAVE
    # --------------------------------------------------
    ax.set_title(cfg["title"], fontsize=10)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / cfg["output_filename"], dpi=cfg["dpi"])
  

    print("Saved:", OUTPUT_DIR / cfg["output_filename"])
