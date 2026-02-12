# -*- coding: utf-8 -*-
"""
RDPS 3h Accumulated Precipitation + Jet Stream (250 hPa wind speed)

RDPS notes:
- RDPS is on RLatLon => latitude/longitude are 2D arrays (y, x)

Supports:
- Standalone mode (creates fig/ax and saves PNG)
- Multi-panel mode (draws onto provided ax)
"""

from __future__ import annotations

import os
from pathlib import Path
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.patches as mpatches
import matplotlib.patheffects as PathEffects
import matplotlib as mpl

import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.feature import NaturalEarthFeature, ShapelyFeature
import geopandas as gpd

from scipy.ndimage import maximum_filter
import matplotlib.tri as mtri

# --------------------------------------------------
# CONFIG (RDPS)
# --------------------------------------------------
PLOT_CONFIG_PCPN3_RDPS = {
    # =====  RDPS 3h precip file  =====
    "pcpn_grib": "data_hpfx/20260109/12/003/20260109T12Z_MSC_RDPS_Precip-Accum3h_Sfc_RLatLon0.09_PT003H.grib2",
  

    # Optional fire boundary
    "fire_outline": "fire_centers_all.geojson",
    "show_fire_boundary": False,
    "fire_facecolor": "none",
    "fire_edgecolor": "0.3",
    "fire_linewidth": 0.4,

    # --- Domain / projection ---
    "central_longitude": -130.0,
    "central_latitude": 50.0,
    "extent": [-160.0, -100.0, 30.0, 70.0],

    # --- Gridlines ---
    "grid_dx": 10,
    "grid_dy": 10,
    "lon_label_value": -140,
    "lat_label_value": 40,

    # --- precip bins (mm) ---
    "show_precip": True,
    "pcpn_bounds_mm": [0.5, 2, 5, 10, 25, 50, 100],
    "pcpn_labels": ["0.5–2", "2–5", "5–10", "10–25", "25–50", "50–100", "100+"],
    "pcpn_bin_colors": [
        "#eef7ed",  # 0.5–2
        "#d9edd7",  # 2–5
        "#bfe3bd",  # 5–10
        "#97c99a",  # 10–25
        "#6fae78",  # 25–50
        "#3f8f5f",  # 50–100
        "#1f6b3f",  # 100+
    ],

    # Whether to mask < 0.5 mm
    "mask_below_mm": 0.5,

    # Contour outline widths
    "outline_lw": 0.6,

    # Hatch linewidth (global rcParam)
    "hatch_linewidth": 0.15,

    # --- Styling ---
    "figsize": (10, 7),
    "dpi": 300,
    "title": "RDPS 3h Accumulated Precipitation (mm)",
    "base_fontsize": 7,
    "axes_linewidth": 0.3,

    # --- Legend ---
    "legend_title": "3h PCPN (mm)",
    "legend_loc": "upper right",
    "legend_fontsize": 7,
    "legend_title_fontsize": 8,

    # --- Output ---
    "output_dir": "outputs",
    "output_filename": "RDPS_3h_Precip_color.png",

    # --- Jet core overlay (250 hPa wind speed) ---
    "show_jet_core": False,
    # Example RDPS naming (adjust):
    # 20260109T12Z_MSC_RDPS_WindSpeed_IsbL-0250_RLatLon0.09_PT006H.grib2
    "jet_spd_grib": "data_hpfx/20260109/12/006/20260109T12Z_MSC_RDPS_WindSpeed_IsbL-0250_RLatLon0.09_PT006H.grib2",
   

    "jet_units": "kt",          # most GRIB winds are m/s; we convert to kt
    "jet_shade1": 80,           # shade >=80 kt
    "jet_shade2": 120,          # shade >=120 kt
    "jet_label_thresh": 100,    # label maxima >=100 kt

    "jet_window": 51,
    "jet_grid_min_dist": 50,    # RDPS dense grid: increase (10 is too small)
    "jet_deg_min_dist": 2.0,
    "jet_max_labels": 8,

    "jet_J_letter_fs": 18,
    "jet_J_value_fs": 9,

    # --- Triangulation control (projected tri) ---
    "tri_stride": 2,               # 1=slow, 2–3 recommended
    "tri_clip_to_extent": False,    # keep points around map
    "tri_clip_pad_deg": 8.0,       # IMPORTANT: prevents hull cutting into the panel
}


# --------------------------------------------------
# Helpers
# --------------------------------------------------
def open_ds(grib_path: Path) -> xr.Dataset:
    """
    RDPS-safe cfgrib open: index file is per-GRIB, not shared.
    This prevents 'older than GRIB' and 'incompatible' warnings.
    """
    grib_path = Path(grib_path)
    idx_path = grib_path.with_suffix(grib_path.suffix + ".idx")  # file.grib2.idx
    return xr.open_dataset(
        grib_path,
        engine="cfgrib",
        backend_kwargs={"indexpath": str(idx_path)},
    )


def get_project_root() -> Path:
    if "__file__" in globals():
        return Path(__file__).resolve().parents[1]
    cwd = Path(os.getcwd()).resolve()
    if cwd.name == "src":
        return cwd.parent
    return cwd


def infer_precip_var(ds: xr.Dataset):
    candidates = ["tp", "APCP", "apcp", "unknown", "precip", "prate"]
    for c in candidates:
        if c in ds.data_vars:
            return ds[c]
    return ds[list(ds.data_vars)[0]]


def to_mm(da: xr.DataArray) -> xr.DataArray:
    units = str(da.attrs.get("units", "")).lower().strip()
    if units in ["m", "meter", "meters", "metre", "metres"]:
        return da * 1000.0
    return da


def _tri_points_projected(lon2, lat2, fld2, extent, proj, pc, stride=2, clip=True, pad_deg=8.0):
    lon_s = lon2[::stride, ::stride]
    lat_s = lat2[::stride, ::stride]
    v_s = fld2[::stride, ::stride]

    lon_min, lon_max, lat_min, lat_max = extent
    lon_min_p = lon_min - pad_deg
    lon_max_p = lon_max + pad_deg
    lat_min_p = lat_min - pad_deg
    lat_max_p = lat_max + pad_deg

    m = np.isfinite(v_s) & np.isfinite(lon_s) & np.isfinite(lat_s)
    if clip:
        m = (
            m &
            (lon_s >= lon_min_p) & (lon_s <= lon_max_p) &
            (lat_s >= lat_min_p) & (lat_s <= lat_max_p)
        )

    lon1 = lon_s[m].ravel()
    lat1 = lat_s[m].ravel()
    v1 = v_s[m].ravel()

    pts = proj.transform_points(pc, lon1, lat1)
    x = pts[:, 0]
    y = pts[:, 1]

    good = np.isfinite(x) & np.isfinite(y) & np.isfinite(v1)
    return x[good], y[good], v1[good]

def build_tri_safe(lon2, lat2, fld2, extent, stride=2, clip=True, max_edge_deg=4.0):
    """
    Build a Triangulation for curvilinear RDPS grids, and mask triangles
    with too-long edges (these are what trigger the Shapely multipolygon crash).
    """
    lon = lon2[::stride, ::stride]
    lat = lat2[::stride, ::stride]
    val = fld2[::stride, ::stride]

    lon_min, lon_max, lat_min, lat_max = extent
    m = np.isfinite(lon) & np.isfinite(lat) & np.isfinite(val)

    if clip:
        m &= (lon >= lon_min) & (lon <= lon_max) & (lat >= lat_min) & (lat <= lat_max)

    x = lon[m].ravel()
    y = lat[m].ravel()
    v = val[m].ravel()

    tri = mtri.Triangulation(x, y)

    # mask triangles with long edges
    tris = tri.triangles
    xtri = x[tris]
    ytri = y[tris]

    e0 = np.hypot(xtri[:, 1] - xtri[:, 0], ytri[:, 1] - ytri[:, 0])
    e1 = np.hypot(xtri[:, 2] - xtri[:, 1], ytri[:, 2] - ytri[:, 1])
    e2 = np.hypot(xtri[:, 0] - xtri[:, 2], ytri[:, 0] - ytri[:, 2])

    bad = (e0 > max_edge_deg) | (e1 > max_edge_deg) | (e2 > max_edge_deg)
    tri.set_mask(bad)

    return tri, v

def add_eccc_precip_legend(ax, cfg):
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
    s1 = int(cfg.get("jet_shade1", 80))
    s2 = int(cfg.get("jet_shade2", 120))

    handles = [
        mpatches.Patch(
            facecolor="white", edgecolor="black", hatch="....",
            label=f"Jet Corridor ≥ {s1} kt", linewidth=0.8
        ),
        mpatches.Patch(
            facecolor="white", edgecolor="black", hatch="........",
            label=f"Jet Core ≥ {s2} kt", linewidth=0.8
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
# MAIN PLOT FUNCTION
# --------------------------------------------------
def plot_pcpn3_rdps(cfg: dict, ax=None):
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
        fig = ax.figure

    extent = cfg["extent"]
    lon_min, lon_max, lat_min, lat_max = extent
    ax.set_extent(extent, crs=pc)

    # --------------------------------------------------
    # 1) LOAD RDPS 3h PCPN
    # --------------------------------------------------
    ds_p = open_ds(ROOT / cfg["pcpn_grib"])
    da = to_mm(infer_precip_var(ds_p).squeeze())

    # RDPS coords are 2D
    lat2 = ds_p["latitude"].values
    lon2 = ds_p["longitude"].values

    P = da.values.astype(np.float64)

    mask_thr = cfg.get("mask_below_mm", 0.5)
    if mask_thr is not None:
        P = np.where(np.isfinite(P), P, 0.0)      # keep grid coverage
        P = np.where(P >= float(mask_thr), P, 0.0)  # dry = 0 mm


    # --------------------------------------------------
    # 2) GRIDLINES + SINGLE LABELS
    # --------------------------------------------------
    gl = ax.gridlines(
        draw_labels=False,
        crs=pc,
        color="black",
        linewidth=0.4,
        alpha=0.4,
        linestyle="dotted",
        zorder=1
    )
    gl.xlocator = mticker.FixedLocator(np.arange(-180, 181, cfg["grid_dx"]))
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
    # 3) BASE MAP FEATURES
    # --------------------------------------------------
    ax.add_feature(cfeature.LAND, facecolor="white", edgecolor="none", zorder=0)
    ax.add_feature(cfeature.COASTLINE, linewidth=0.6, zorder=13)
    ax.add_feature(cfeature.BORDERS, linewidth=0.5, zorder=13)

    provinces = NaturalEarthFeature(
        "cultural", "admin_1_states_provinces_lines", "50m", facecolor="none"
    )
    ax.add_feature(provinces, edgecolor="black", linewidth=0.6, zorder=13)

    if cfg.get("show_fire_boundary", False):
        try:
            fire_gdf = gpd.read_file(ROOT / cfg["fire_outline"])
            fire_feature = ShapelyFeature(fire_gdf.geometry, crs=pc)
            ax.add_feature(
                fire_feature,
                facecolor=cfg.get("fire_facecolor", "none"),
                edgecolor=cfg.get("fire_edgecolor", "0.3"),
                linewidth=cfg.get("fire_linewidth", 0.4),
                zorder=7,
            )
        except Exception as e:
            print("Warning: fire boundary not drawn:", e)

    # --------------------------------------------------
    # 4) PROJECTED TRI POINTS (fix scope)
    # --------------------------------------------------
    stride = int(cfg.get("tri_stride", 2))
    clip = bool(cfg.get("tri_clip_to_extent", True))
    pad_deg = float(cfg.get("tri_clip_pad_deg", 8.0))

    xP, yP, vP = _tri_points_projected(lon2, lat2, P, extent, proj, pc,
                                       stride=stride, clip=clip, pad_deg=pad_deg)

    # --------------------------------------------------
    # 5) PCPN DISCRETE SHADING + OUTLINES
    # --------------------------------------------------
    if cfg.get("show_precip", True):
        bounds = np.array(cfg["pcpn_bounds_mm"], dtype=float)
        levels = np.concatenate(([-1e9], bounds, [1e9]))
        bin_colors = cfg["pcpn_bin_colors"]

        ax.tricontourf(
            xP, yP, vP,
            levels=levels,
            colors=[(1,1,1,0)] + bin_colors,
            extend="max",
            antialiased=True,
            zorder=9,
        )

        ax.tricontour(
            xP, yP, vP,
            levels=bounds,
            colors="black",
            linewidths=cfg.get("outline_lw", 0.6),
            zorder=10,
        )

    # --------------------------------------------------
    # 6) Jet-core shading + "J" maxima markers (RDPS 2D)
    # --------------------------------------------------
    if cfg.get("show_jet_core", False):

        def _thin_pts_grid(iy, ix, min_dist=25):
            kept = []
            for j in range(len(iy)):
                y, x = int(iy[j]), int(ix[j])
                ok = True
                for k in kept:
                    dy = y - int(iy[k])
                    dx = x - int(ix[k])
                    if (dy * dy + dx * dx) < (min_dist * min_dist):
                        ok = False
                        break
                if ok:
                    kept.append(j)
            return kept

        def _thin_latlon(pts, min_deg=2.0):
            # pts entries: (val, y, x, lat, lon)
            pts.sort(reverse=True, key=lambda t: t[0])
            kept, kept_latlon = [], []
            for val, y, x, lat, lon in pts:
                too_close = False
                for klat, klon in kept_latlon:
                    dlat = lat - klat
                    dlon = (lon - klon) * np.cos(np.radians((lat + klat) / 2.0))
                    if (dlat*dlat + dlon*dlon) < (min_deg*min_deg):
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
        js_da = list(ds_js.data_vars.values())[0].squeeze()
        JS = js_da.values.astype(np.float64)

        # RDPS coords for jet (should match precip grid, but don't assume)
        lat2_js = ds_js["latitude"].values
        lon2_js = ds_js["longitude"].values

        # Convert to kt if needed (usually m/s in GRIB)
        jet_units = str(cfg.get("jet_units", "kt")).lower()
        if jet_units in ["kt", "kts", "knots"]:
            JS = JS * 1.943844

        s1 = float(cfg.get("jet_shade1", 80))
        s2 = float(cfg.get("jet_shade2", 120))

        # Projected tri points for jet field
        xJ, yJ, vJ = _tri_points_projected(lon2_js, lat2_js, JS, extent, proj, pc,
                                           stride=stride, clip=clip, pad_deg=pad_deg)

        old_hlw = mpl.rcParams.get("hatch.linewidth", 1.0)
        mpl.rcParams["hatch.linewidth"] = 0.25

        # corridor (>= s1, < s2)
        ax.tricontourf(
            xJ, yJ, vJ,
            levels=[s1, s2],
            colors=["none"],
            hatches=["...."],
            zorder=11,
        )

        # core (>= s2)
        ax.tricontourf(
            xJ, yJ, vJ,
            levels=[s2, 9999],
            colors=["none"],
            hatches=["........"],
            zorder=12,
        )

        mpl.rcParams["hatch.linewidth"] = old_hlw

        # outline for jet thresholds
        ax.tricontour(
            xJ, yJ, vJ,
            levels=[s1, s2],
            colors="black",
            linewidths=0.5,
            zorder=10,
        )

        # ---- maxima labels in grid space ----
        win = int(cfg.get("jet_window", 51))
        jsmax = maximum_filter(JS, size=win)
        is_max = (JS == jsmax)

        label_thresh = float(cfg.get("jet_label_thresh", 100))
        is_max = is_max & (JS >= label_thresh)

        iy, ix = np.where(is_max)
        if iy.size > 0:
            keep = _thin_pts_grid(iy, ix, min_dist=int(cfg.get("jet_grid_min_dist", 25)))
            iy2 = iy[keep]
            ix2 = ix[keep]

            pts = []
            for y, x in zip(iy2, ix2):
                lat = float(lat2_js[y, x])
                lon = float(lon2_js[y, x])
                val = float(JS[y, x])
                if (lon_min <= lon <= lon_max) and (lat_min <= lat <= lat_max):
                    pts.append((val, y, x, lat, lon))

            kept = _thin_latlon(pts, min_deg=float(cfg.get("jet_deg_min_dist", 2.0)))
            max_labels = int(cfg.get("jet_max_labels", 8))

            for val, y, x, lat, lon in kept[:max_labels]:
                _draw_J(ax, lon, lat, val)

    # --------------------------------------------------
    # 7) Legends (works in multi-panel too)
    # --------------------------------------------------
    
    if cfg.get("show_jet_core", True):
        add_jet_legend(ax, cfg)
    
    if cfg.get("show_precip", True):
        precip_leg = add_eccc_precip_legend(ax, cfg)
        ax.add_artist(precip_leg)
    # --- Force map frame (projection boundary) to draw everywhere ---
    try:
        ax.spines["geo"].set_visible(True)
        ax.spines["geo"].set_edgecolor("black")
        ax.spines["geo"].set_linewidth(0.8)
        ax.spines["geo"].set_zorder(1000)
    except Exception:
        # older Cartopy fallback
        ax.outline_patch.set_visible(True)
        ax.outline_patch.set_edgecolor("black")
        ax.outline_patch.set_linewidth(0.8)
        ax.outline_patch.set_zorder(1000)

    # --------------------------------------------------
    # 8) Title + save
    # --------------------------------------------------
    if standalone:
        ax.set_title(cfg["title"], fontsize=10)
        outpath = OUTPUT_DIR / cfg["output_filename"]
        plt.savefig(outpath, dpi=cfg["dpi"])
        print("Saved:", outpath)
    else:
        ax.set_title("")

    return ax


if __name__ == "__main__":
    plot_pcpn3_rdps(PLOT_CONFIG_PCPN3_RDPS)
