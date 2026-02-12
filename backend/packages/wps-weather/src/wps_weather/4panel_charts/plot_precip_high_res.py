# -*- coding: utf-8 -*-
"""
GDPS 12/6h Accumulated Precipitation + Jet Stream
"""

import os
from pathlib import Path
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.patheffects as PathEffects
import matplotlib.patches as mpatches

import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.feature import NaturalEarthFeature, ShapelyFeature
import geopandas as gpd
from scipy.ndimage import maximum_filter
import matplotlib as mpl
from cartopy.util import add_cyclic_point
import time

t0 = time.perf_counter()
# --------------------------------------------------
# DEFAULT CONFIG (all feature values are here)
# --------------------------------------------------
PLOT_CONFIG_PCPN12 = {
    # =====  Precip file  =====
    "pcpn_grib": "data/20251218T12Z_MSC_GDPS_Precip-Accum12h_Sfc_LatLon0.15_PT012H.grib2",
    "pcpn_index": "pcpn12.idx",

    # Optional fire boundary
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
    "grid_dx": 10,
    "grid_dy": 10,
    "lon_label_value": -140,
    "lat_label_value": 40,

    # --- precip bins (mm) ---
    "show_precip": True,   # allow jet-only panel
    "pcpn_bounds_mm": [0.5, 2, 5, 10, 25, 50, 100],
    "pcpn_hatches_for_bins": ["....", "xxxx", "////", "\\\\\\\\", "++++", "####"],

    # More Greens Style
    "pcpn_labels": ["0.5–2", "2–5", "5-10", "10–25", "25–50", "50–100", "100+"],
    "pcpn_bin_colors": [
        "#eef7ed",  # 0.5–2
        "#d9edd7",  # 2–5
        "#bfe3bd",  # 5–10
        "#97c99a",  # 10–25
        "#6fae78",  # 25–50
        "#3f8f5f",  # 50–100
        "#1f6b3f",  # 100+
    ],

    # Whether to mask < 0.5 mm (keeps map clean like ECCC)
    "mask_below_mm": 0.5,

    # Contour outline widths
    "outline_lw": 0.5,

    # Hatch linewidth 
    "hatch_linewidth": 0.15,

    # --- Styling ---
    "figsize": (10, 7),
    "dpi": 300,
    "title": "GDPS 12h Accumulated Precipitation (mm)",
    "base_fontsize": 7,
    "axes_linewidth": 0.3,

    # --- Legend ---
    "legend_title": "12h PCPN (mm)",
    "legend_loc": "upper right",
    "legend_fontsize": 7,
    "legend_title_fontsize": 8,

    # --- Output ---
    "output_dir": "outputs",
    "output_filename": "GDPS_12h_Precip_color.png",

    # --- Jet core overlay (250 hPa wind speed) ---
    "show_jet_core": False,
    "jet_spd_grib": "data/20251218T12Z_MSC_GDPS_WindSpeed_IsbL-0250_LatLon0.15_PT012H.grib2",
    "jet_spd_index": "wspd250.idx",

    "jet_units": "kt",          # GDPS wind speed is m/s; we convert to kt
    "jet_shade1": 80,           # shade >=80 kt (jet corridor)
    "jet_shade2": 120,          # darker shade >=120 kt (jet core)
    "jet_label_thresh": 100,    # label maxima >=100 kt

    "jet_window": 51,           # maxima filter size (31–51 good)
    "jet_grid_min_dist": 50,    # first thinning (grid points)
    "jet_deg_min_dist": 2.0,    # second thinning (degrees)
    "jet_max_labels": 8,        # max J labels on map

    "jet_shade1_color": "0.85",
    "jet_shade2_color": "0.70",
    "jet_J_letter_fs": 18,
    "jet_J_value_fs": 9,
}


# --------------------------------------------------
# Helpers
# --------------------------------------------------
def open_ds(grib_path: Path):
    grib_path = Path(grib_path)
    idx_path = grib_path.with_suffix(grib_path.suffix + ".idx")
    return xr.open_dataset(
        grib_path,
        engine="cfgrib",
        backend_kwargs={"indexpath": str(idx_path)},
    )



def get_project_root():
    """Return project root (works in script and Jupyter)."""
    if "__file__" in globals():
        return Path(__file__).resolve().parents[1]
    cwd = Path(os.getcwd()).resolve()
    if cwd.name == "src":
        return cwd.parent
    return cwd


def wrap_lon_180(lons_1d):
    """Wrap 0..360 -> -180..180 and return wrapped + sort order."""
    lon_wrapped = ((lons_1d + 180.0) % 360.0) - 180.0
    order = np.argsort(lon_wrapped)
    return lon_wrapped[order], order


def infer_precip_var(ds: xr.Dataset):
    """Pick precip variable robustly."""
    candidates = ["tp", "APCP", "apcp", "unknown", "precip", "prate"]
    for c in candidates:
        if c in ds.data_vars:
            return ds[c]
    return ds[list(ds.data_vars)[0]]


def to_mm(da: xr.DataArray) -> xr.DataArray:
    """Convert to mm if needed"""
    units = str(da.attrs.get("units", "")).lower().strip()
    if units in ["m", "meter", "meters", "metre", "metres"]:
        return da * 1000.0
    return da


def add_eccc_precip_legend(ax, cfg):
    """Add a small legend inside the map."""
    labels = cfg["pcpn_labels"]
    bin_colors = cfg["pcpn_bin_colors"]

    handles = [
        mpatches.Patch(facecolor=col, edgecolor="black", label=lab, linewidth=0.8)
        for lab, col in zip(labels, bin_colors)
    ]

    leg = ax.legend(
        handles=handles,
        title=cfg["legend_title"],
        loc=cfg["legend_loc"],
        fontsize=cfg["legend_fontsize"],
        title_fontsize=cfg["legend_title_fontsize"],
        frameon=True,
        framealpha=1.0,
        fancybox=False,
        borderpad=0.6,
        labelspacing=0.35,
        handlelength=1.6,
    )
    leg.get_frame().set_edgecolor("black")
    leg.get_frame().set_linewidth(0.8)
    leg.get_frame().set_facecolor("white")
    leg.set_zorder(100)
    return leg


def add_jet_legend(ax, cfg):
    """Legend for jet-core stipple shading."""
    s1 = int(cfg.get("jet_shade1", 80))
    s2 = int(cfg.get("jet_shade2", 120))

    handles = [
        mpatches.Patch(
            facecolor="white",
            edgecolor="black",
            hatch="....",
            label=f"Jet Corridor ≥ {s1} kt",
            linewidth=0.8
        ),
        mpatches.Patch(
            facecolor="white",
            edgecolor="black",
            hatch="........",
            label=f"Jet Core ≥ {s2} kt",
            linewidth=0.8
        ),
    ]

    leg = ax.legend(
        handles=handles,
        title="250hPa Jet",
        loc="lower right",
        fontsize=7,
        title_fontsize=8,
        frameon=True,
        framealpha=1.0,
        fancybox=False,
        borderpad=0.6,
        labelspacing=0.4,
        handlelength=2.0,
        handleheight=1.2,
    )
    leg.get_frame().set_edgecolor("black")
    leg.get_frame().set_linewidth(0.8)
    leg.get_frame().set_facecolor("white")
    leg.set_zorder(100)
    return leg


# --------------------------------------------------
# MAIN PLOT FUNCTION (standalone OR 4-panel)
# --------------------------------------------------
def plot_pcpn12(cfg: dict, ax=None):
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

    standalone = (ax is None)
    if standalone:
        fig = plt.figure(figsize=cfg["figsize"])
        ax = plt.axes(projection=proj)
    else:
        fig = ax.figure  # for completeness

    # --------------------------------------------------
    # 1. LOAD 12h PCPN
    # --------------------------------------------------
    t = time.perf_counter()
    ds_p = open_ds(ROOT / cfg["pcpn_grib"])
    print("pcpn open_ds:", time.perf_counter()-t)
    try: 
       da = to_mm(infer_precip_var(ds_p).squeeze())
    finally:
       ds_p.close()
       
    lats = ds_p["latitude"].values
    lons = ds_p["longitude"].values
    lon_plot, order = wrap_lon_180(lons)
    
    t = time.perf_counter()
    P0 = da.values[:, order].astype(np.float64)
    
    # --- IMPORTANT FIX ---
    # outlines need dry-side values so 0.5 contour exists
    P_outline = np.where(np.isfinite(P0), P0, 0.0)

    thr = cfg.get("mask_below_mm", 0.5)
    if thr is not None:
        P_shade = np.where(P_outline >= float(thr), P_outline, np.nan)
    else:
        P_shade = P_outline.copy()
    
    # use the ORIGINAL lon_plot for both fields
    P_outline_cyc, lon_plot_cyc = add_cyclic_point(P_outline, coord=lon_plot)
    P_shade_cyc, _            = add_cyclic_point(P_shade,   coord=lon_plot)
    
    # overwrite after both are done
    P_outline = P_outline_cyc
    P_shade   = P_shade_cyc
    lon_plot  = lon_plot_cyc
    
    print("pcpn extract:", time.perf_counter()-t)
    
    lon_min, lon_max, lat_min, lat_max = cfg["extent"]
    ax.set_extent(cfg["extent"], crs=pc)

    # --------------------------------------------------
    # 3. GRIDLINES + SINGLE LABELS
    # --------------------------------------------------
    gl = ax.gridlines(
        draw_labels=False,
        crs=pc,
        color="black",
        linewidth=0.4,
        alpha=0.4,
        linestyle="dotted",
        zorder=0
    )

    # --- FIX: keep -180 line back ---
    dx = cfg["grid_dx"]
    gl.xlocator = mticker.FixedLocator(np.arange(-180, 181, dx))
    gl.ylocator = mticker.FixedLocator(np.arange(0, 91, cfg["grid_dy"]))
    
    

    ax.text(
        cfg["lon_label_value"], lat_max - 1.5,
        f"{abs(cfg['lon_label_value'])}W",
        transform=pc,
        fontsize=7, alpha=0.65,
        ha="center", va="center",
        zorder=50
    )
    ax.text(
        lon_min + 1.5, cfg["lat_label_value"],
        f"{cfg['lat_label_value']}N",
        transform=pc,
        fontsize=7, alpha=0.65,
        ha="center", va="center",
        zorder=50
    )

    # --------------------------------------------------
    # 4. BASE MAP FEATURES
    # --------------------------------------------------
    ax.add_feature(cfeature.LAND, facecolor="white", edgecolor="none", zorder=2)
    ax.add_feature(cfeature.COASTLINE, linewidth=0.5, zorder=20)
    ax.add_feature(cfeature.BORDERS, linewidth=0.4, zorder=20)

    provinces = NaturalEarthFeature(
        "cultural", "admin_1_states_provinces_lines", "50m", facecolor="none"
    )
    ax.add_feature(provinces, edgecolor="black", linewidth=0.5, zorder=20)

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
    # 5. PCPN DISCRETE SHADING + OUTLINES
    # --------------------------------------------------
    if cfg.get("show_precip", True):
        bounds = np.array(cfg["pcpn_bounds_mm"], dtype=float)
        levels = np.concatenate(([-1e9], bounds, [1e9]))  # under, bins, over
        bin_colors = cfg["pcpn_bin_colors"]
       
        t = time.perf_counter()
        # shading uses masked field
        ax.contourf(
            lon_plot, lats, P_shade,
            levels=levels,
            colors=["none"] + bin_colors,
            transform=pc,
            extend="max",
            antialiased=True,
            zorder=15,
        )

        # outlines use P_outline (dry side = 0) so 0.5 contour exists
        ax.contour(
            lon_plot, lats, P_outline,
            levels=bounds,
            colors="black",
            linewidths=cfg.get("outline_lw", 0.6),
            transform=pc,
            zorder=15,
        )
        print("pcpn contourf:", time.perf_counter()-t)

    # --------------------------------------------------
    # 5c. Jet-core shading + "J" maxima markers
    # --------------------------------------------------
    if cfg.get("show_jet_core", True):

        def _thin_pts(iy, ix, min_dist=10):
            kept = []
            for j in range(len(iy)):
                y, x = iy[j], ix[j]
                if all((y - iy[k])**2 + (x - ix[k])**2 >= min_dist**2 for k in kept):
                    kept.append(j)
            return kept

        def _thin_latlon(points, min_deg=2.0):
            points.sort(reverse=True, key=lambda t: t[0])
            kept, kept_latlon = [], []
            for val, y, x, lat, lon in points:
                too_close = False
                for klat, klon in kept_latlon:
                    dlat = lat - klat
                    dlon = (lon - klon) * np.cos(np.radians((lat + klat) / 2.0))
                    if (dlat*dlat + dlon*dlon) < min_deg*min_deg:
                        too_close = True
                        break
                if not too_close:
                    kept.append((val, y, x, lat, lon))
                    kept_latlon.append((lat, lon))
            return kept

        def _draw_J(ax, lon, lat, val):
            pad = 1.0
            if lon < lon_min + pad or lon > lon_max - pad or lat < lat_min + pad or lat > lat_max - pad:
                return

            t1 = ax.text(
                lon, lat, "J",
                transform=pc,
                ha="center", va="center",
                fontsize=cfg.get("jet_J_letter_fs", 18),
                fontweight="bold",
                color="black", zorder=30
            )
            t1.set_path_effects([
                PathEffects.Stroke(linewidth=3, foreground="white"),
                PathEffects.Normal()
            ])

            t2 = ax.text(
                lon, lat - 2, f"{int(val)}",
                transform=pc,
                ha="center", va="center",
                fontsize=cfg.get("jet_J_value_fs", 9),
                fontweight="bold",
                color="black", zorder=30
            )
            t2.set_path_effects([
                PathEffects.Stroke(linewidth=2, foreground="white"),
                PathEffects.Normal()
            ])

        ds_js = open_ds(ROOT / cfg["jet_spd_grib"])
        try:
           js_da = list(ds_js.data_vars.values())[0].squeeze()
        finally:
           ds_js.close()
        JS = js_da.values[:, order].astype(np.float64)

        jet_units = str(cfg.get("jet_units", "kt")).lower()
        if jet_units in ["kt", "kts", "knots"]:
            JS = JS * 1.943844  # m/s -> kt

        s1 = float(cfg.get("jet_shade1", 80))
        s2 = float(cfg.get("jet_shade2", 120))

        old_hlw = mpl.rcParams.get("hatch.linewidth", 1.0)
        mpl.rcParams["hatch.linewidth"] = 0.25

        ax.contourf(
            lon_plot, lats, JS,
            levels=[s1, s2],
            colors=["none"],
            hatches=["...."],
            transform=pc,
            zorder=9,
        )

        ax.contourf(
            lon_plot, lats, JS,
            levels=[s2, 9999],
            colors=["none"],
            hatches=["........"],
            transform=pc,
            zorder=9,
        )

        mpl.rcParams["hatch.linewidth"] = old_hlw

        ax.contour(
            lon_plot, lats, JS,
            levels=[s1, s2],
            colors="black",
            linewidths=0.5,
            transform=pc,
            zorder=8,
        )

        win = int(cfg.get("jet_window", 41))
        jsmax = maximum_filter(JS, size=win)
        is_max = (JS == jsmax)

        label_thresh = float(cfg.get("jet_label_thresh", 100))
        is_max = is_max & (JS >= label_thresh)

        iy, ix = np.where(is_max)
        if iy.size > 0:
            keep = _thin_pts(iy, ix, min_dist=int(cfg.get("jet_grid_min_dist", 10)))
            iy2 = iy[keep]
            ix2 = ix[keep]

            pts = []
            for y, x in zip(iy2, ix2):
                lat = float(lats[y])
                lon = float(lon_plot[x])
                val = float(JS[y, x])
                if (lon_min <= lon <= lon_max) and (lat_min <= lat <= lat_max):
                    pts.append((val, y, x, lat, lon))

            kept = _thin_latlon(pts, min_deg=float(cfg.get("jet_deg_min_dist", 2.0)))
            max_labels = int(cfg.get("jet_max_labels", 8))

            for val, y, x, lat, lon in kept[:max_labels]:
                _draw_J(ax, lon, lat, val)

    # --------------------------------------------------
    # 6. Legends
    # --------------------------------------------------
    if cfg.get("show_jet_core", True):
        jet_leg = add_jet_legend(ax, cfg)
    if cfg.get("show_precip", True):
        precip_leg = add_eccc_precip_legend(ax, cfg)
        ax.add_artist(precip_leg)

    # --------------------------------------------------
    # 7. Hard mask border
    # --------------------------------------------------

    frame = mpatches.Rectangle(
        (0, 0), 1, 1,
        transform=ax.transAxes,
        fill=False,
        edgecolor="black",
        linewidth=1.5,
        zorder=10_000
    )
    ax.add_patch(frame)

    # --------------------------------------------------
    # 8. Saving figure
    # --------------------------------------------------
    if standalone:
        outpath = OUTPUT_DIR / cfg["output_filename"]
        plt.savefig(outpath, dpi=cfg["dpi"])
        print("Saved:", outpath)

    return ax

if __name__ == "__main__":
    plot_pcpn12(PLOT_CONFIG_PCPN12)
