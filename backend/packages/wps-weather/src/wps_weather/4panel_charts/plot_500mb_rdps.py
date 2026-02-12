# -*- coding: utf-8 -*-
"""
RDPS 500 hPa Height (dam) + Absolute Vorticity (1e-5 s^-1).

Key points (RDPS curvilinear grid):
- RDPS lat/lon are 2D (y, x)
- Use tricontour over (lon,lat) points with PlateCarree transform

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

from scipy.ndimage import maximum_filter, minimum_filter, gaussian_filter, label
import geopandas as gpd
import matplotlib.tri as mtri


# --------------------------------------------------
# CONFIG (RDPS)
# --------------------------------------------------
CFG_500 = {
    # --- Input files (example) ---
    "z500_grib": "data_hpfx/20260202/12/015/20260202T12Z_MSC_RDPS_GeopotentialHeight_IsbL-0500_RLatLon0.09_PT015H.grib2",
    "vort_grib": "data_hpfx/20260202/12/015/20260202T12Z_MSC_RDPS_AbsoluteVorticity_IsbL-0500_RLatLon0.09_PT015H.grib2",
    "valid_time_str": "F003 Valid: Tue 2026-01-12 15Z",
    "fire_outline": "fire_centers_all.geojson",

    # --- Domain / projection ---
    "central_longitude": -130.0,
    "central_latitude": 50.0,
    "extent": [-160.0, -100.0, 30.0, 70.0],  # lon_min, lon_max, lat_min, lat_max

    # --- Gridlines ---
    "grid_dx": 10,
    "grid_dy": 10,
    "lon_label_value": -140,
    "lat_label_value": 40,

    # --- 500 hPa heights ---
    "height_interval": 6,
    "height_range": [480, 600],
    "height_highlight": [528, 546, 570],
    "height_label_lon": -140.0,
    "height_label_tol": 3.0,
    "height_label_min_dlat": 0.7,

    # --- Vorticity (absolute) ---
    "vort_levels": list(np.arange(0, 16, 8)),
    "vort_linewidth": 0.5,
    "vort_linestyle": "dashed",

    # --- Vort symbols (+/-) ---
    "vort_threshold": 0.0,
    "vort_window": 39,
    "vort_grid_min_dist": 10,
    "vort_symbol_fontsize": 5,
    "vort_value_fontsize": 5,
    "vort_label_positive_only": False,

    # --- H/L centres ---
    "hl_window": 41,
    "hl_grid_min_dist": 25,      # grid-space thinning (optional fallback)
    "hl_deg_min_dist": 5,        # distance thinning in degrees (main dedupe control)
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

    # --- Smoothing ---
    "smooth_height_sigma": 0.0,
    "smooth_vort_sigma": 0.6,

    # --- tricontour speed/stability control ---
    "tri_stride": 2,              # 1=full res, 2–3 recommended
    "tri_clip_to_extent": False,   # recommended for speed + stability
    "tri_max_edge_deg": 4.0,      # mask triangles with edges longer than this (deg)

    # --- Styling ---
    "base_fontsize": 7,
    "axes_linewidth": 0.3,
    "coastline_lw": 0.5,
    "borders_lw": 0.4,
    "province_lw": 0.5,

    # --- Output ---
    "output_dir": "outputs",
    "output_filename": "RDPS_500hPa_Height_AbsVorticity.png",
    "dpi": 300,
    "figsize": (10, 7),
    "title": "RDPS 500 hPa Height (dam) + Absolute Vorticity (1e-5 s⁻¹)",
}


# --------------------------------------------------
# Helpers
# --------------------------------------------------
def get_project_root() -> Path:
    if "__file__" in globals():
        return Path(__file__).resolve().parents[1]
    cwd = Path(os.getcwd()).resolve()
    if cwd.name == "src":
        return cwd.parent
    return cwd


def open_ds(grib_path: Path) -> xr.Dataset:
    """Open a GRIB2 file using cfgrib with a persistent .idx file."""
    grib_path = Path(grib_path)
    idx_path = grib_path.with_suffix(grib_path.suffix + ".idx")
    return xr.open_dataset(
        grib_path,
        engine="cfgrib",
        backend_kwargs={"indexpath": str(idx_path)},
    )


def draw_HL(ax, lon, lat, letter, val, pc, lon_min, lon_max, lat_min, lat_max, cfg):
    d_letter = 1.5
    d_value = 1.2
    lat_letter = lat + d_letter
    lat_value = lat - d_value

    pad_lon, pad_lat = 1.0, 1.0
    if (lon < lon_min + pad_lon or lon > lon_max - pad_lon or
        lat_letter > lat_max - pad_lat or lat_value < lat_min + pad_lat):
        return

    txt = ax.text(
        lon, lat_letter, letter, transform=pc,
        ha="center", va="center",
        fontsize=cfg["hl_letter_fontsize"], fontweight="bold",
        color="black", zorder=12
    )
    txt.set_path_effects([PathEffects.Stroke(linewidth=3, foreground="white"), PathEffects.Normal()])

    circ = ax.text(lon, lat, "⊗", transform=pc, ha="center", va="center",
                   fontsize=10, color="black", zorder=12)
    circ.set_path_effects([PathEffects.Stroke(linewidth=2, foreground="white"), PathEffects.Normal()])

    num = ax.text(
        lon, lat_value, f"{int(val)}", transform=pc,
        ha="center", va="center",
        fontsize=cfg["hl_value_fontsize"], fontweight="bold",
        color="black", zorder=12
    )
    num.set_path_effects([PathEffects.Stroke(linewidth=2, foreground="white"), PathEffects.Normal()])


def draw_vort_symbol(ax, lon, lat, sign, value, pc, lon_min, lon_max, lat_min, lat_max, cfg):
    pad = 0.5
    if not (lon_min + pad <= lon <= lon_max - pad and lat_min + pad <= lat <= lat_max - pad):
        return

    fs_s = cfg["vort_symbol_fontsize"]
    fs_v = cfg["vort_value_fontsize"]

    txt = ax.text(lon, lat + 0.4, sign, transform=pc, ha="center", va="center",
                  fontsize=fs_s, color="black", zorder=10)
    txt.set_path_effects([PathEffects.Stroke(linewidth=1.8, foreground="white"), PathEffects.Normal()])

    val_txt = ax.text(lon, lat - 0.3, f"{int(abs(value))}", transform=pc, ha="center", va="center",
                      fontsize=fs_v, color="black", zorder=10)
    val_txt.set_path_effects([PathEffects.Stroke(linewidth=1.5, foreground="white"), PathEffects.Normal()])


def build_tri_safe(lon2, lat2, fld2, extent, stride=2, clip=True, max_edge_deg=4.0):
    """
    Build Triangulation for curvilinear grid and mask triangles with too-long edges.
    This prevents Cartopy/Shapely MultiPolygon projection crashes.
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

    tris = tri.triangles
    xtri = x[tris]
    ytri = y[tris]

    e0 = np.hypot(xtri[:, 1] - xtri[:, 0], ytri[:, 1] - ytri[:, 0])
    e1 = np.hypot(xtri[:, 2] - xtri[:, 1], ytri[:, 2] - ytri[:, 1])
    e2 = np.hypot(xtri[:, 0] - xtri[:, 2], ytri[:, 0] - ytri[:, 2])

    bad = (e0 > max_edge_deg) | (e1 > max_edge_deg) | (e2 > max_edge_deg)
    tri.set_mask(bad)

    return tri, v


def pick_one_per_component(mask: np.ndarray, val2d: np.ndarray, prefer="centroid"):
    """
    Pick one point per connected component (plateau blob).
    Force 8-connected labeling so diagonal plateau cells are merged.
    Returns list of (y, x, value).
    """
    structure = np.ones((3, 3), dtype=int)  # 8-connected
    lab, nlab = label(mask, structure=structure)

    picks = []
    for k in range(1, nlab + 1):
        pts = np.argwhere(lab == k)
        if pts.size == 0:
            continue

        if prefer == "centroid":
            cy, cx = pts.mean(axis=0)
            d2 = (pts[:, 0] - cy) ** 2 + (pts[:, 1] - cx) ** 2
            y, x = pts[np.argmin(d2)]
        elif prefer == "median":
            y = int(np.median(pts[:, 0]))
            x = int(np.median(pts[:, 1]))
        else:
            y, x = pts[0]

        picks.append((int(y), int(x), float(val2d[int(y), int(x)])))
    return picks


def thin_by_distance_latlon(points, min_deg=2.0, prefer="high"):
    """
    points: list of (y,x,val,lat,lon)
    Keep only one point if another is within min_deg (degree distance approx).
    - prefer="high": keeps higher val first (good for highs)
    - prefer="low" : keeps lower val first (good for lows)
    """
    if prefer == "low":
        points_sorted = sorted(points, key=lambda t: t[2])  # low first
    else:
        points_sorted = sorted(points, key=lambda t: t[2], reverse=True)  # high first

    kept = []
    kept_ll = []
    for y, x, val, lat, lon in points_sorted:
        ok = True
        for klat, klon in kept_ll:
            dlat = lat - klat
            dlon = (lon - klon) * np.cos(np.radians((lat + klat) / 2.0))
            if (dlat * dlat + dlon * dlon) < (min_deg * min_deg):
                ok = False
                break
        if ok:
            kept.append((y, x, val, lat, lon))
            kept_ll.append((lat, lon))
    return kept


def add_boxed_height_labels_rdps(ax, lon2, lat2, Z, cfg, pc, extent):
    """
    Approx of GDPS boxed labels along a target longitude, adapted for 2D lon/lat.
    """
    lon_target = float(cfg.get("height_label_lon", -140.0))
    tol_lon = 0.35
    lon_min, lon_max, lat_min, lat_max = extent

    m = (
        np.isfinite(Z) &
        (np.abs(lon2 - lon_target) <= tol_lon) &
        (lon2 >= lon_min) & (lon2 <= lon_max) &
        (lat2 >= lat_min) & (lat2 <= lat_max)
    )
    if not np.any(m):
        return

    cand_lat = lat2[m]
    cand_Z = Z[m]

    hmin, hmax = cfg["height_range"]
    hlev = np.arange(hmin, hmax, cfg["height_interval"])

    used_lats = []
    for lev in hlev:
        idx = int(np.argmin(np.abs(cand_Z - lev)))
        if float(np.abs(cand_Z[idx] - lev)) > float(cfg.get("height_label_tol", 3.0)):
            continue

        lat_lab = float(cand_lat[idx])
        if any(abs(lat_lab - u) < float(cfg.get("height_label_min_dlat", 0.7)) for u in used_lats):
            continue
        used_lats.append(lat_lab)

        ax.text(
            lon_target, lat_lab, f"{int(lev)}",
            transform=pc, ha="center", va="center",
            fontsize=8, color="white",fontweight="bold",
            bbox=dict(boxstyle="square,pad=0.1", facecolor="black",
                      edgecolor="black", linewidth=0.6),
            zorder=8
        )


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
    proj = ccrs.LambertConformal(
        central_longitude=cfg["central_longitude"],
        central_latitude=cfg["central_latitude"]
    )

    standalone = (ax is None)
    if standalone:
        fig = plt.figure(figsize=cfg["figsize"])
        ax = plt.axes(projection=proj)
        ax.set_title(cfg["title"], fontsize=10)
    else:
        fig = ax.figure
        ax.set_title("")

    extent = cfg["extent"]
    lon_min, lon_max, lat_min, lat_max = extent
    ax.set_extent(extent, crs=pc)

    # --- Load data ---
    ds_z500 = open_ds(ROOT / cfg["z500_grib"])
    ds_vort = open_ds(ROOT / cfg["vort_grib"])

    z = ds_z500[list(ds_z500.data_vars)[0]].squeeze()
    v = ds_vort[list(ds_vort.data_vars)[0]].squeeze()

    # Height to dam
    H500 = z / 10.0 if float(z.max()) > 1000 else z

    # Abs vort to 1e-5 s^-1
    VORT = v * 1e5

    # RDPS: lat/lon are 2D
    lat2 = ds_z500["latitude"].values
    lon2 = ds_z500["longitude"].values

    Z = H500.values.astype(np.float64)
    V = VORT.values.astype(np.float64)

    # optional smoothing
    sigZ = float(cfg.get("smooth_height_sigma", 0.0))
    sigV = float(cfg.get("smooth_vort_sigma", 0.0))
    if sigZ > 0:
        Z = gaussian_filter(Z, sigma=sigZ)
    if sigV > 0:
        V = gaussian_filter(V, sigma=sigV)

    # --- Gridlines + single labels ---
    gl = ax.gridlines(draw_labels=False, crs=pc, color="black", linewidth=0.4,
                      alpha=0.4, linestyle="dotted")
    gl.xlocator = mticker.FixedLocator(np.arange(-180, 181, cfg["grid_dx"]))
    gl.ylocator = mticker.FixedLocator(np.arange(0, 91, cfg["grid_dy"]))

    ax.text(cfg["lon_label_value"], lat_max - 1.5, f"{abs(cfg['lon_label_value'])}W",
            transform=pc, fontsize=7, alpha=0.65, ha="center", va="center")
    ax.text(lon_min + 1.5, cfg["lat_label_value"], f"{cfg['lat_label_value']}N",
            transform=pc, fontsize=7, alpha=0.65, ha="center", va="center")

    # --- Base map ---
    ax.add_feature(cfeature.LAND, edgecolor="black", facecolor="white", linewidth=0.4, zorder=0)
    ax.add_feature(cfeature.COASTLINE, linewidth=cfg["coastline_lw"], zorder=12)
    ax.add_feature(cfeature.BORDERS, linewidth=cfg["borders_lw"], zorder=12)

    provinces = NaturalEarthFeature("cultural", "admin_1_states_provinces_lines", "50m", facecolor="none")
    ax.add_feature(provinces, edgecolor="black", linewidth=cfg["province_lw"], zorder=13)

    if cfg.get("show_fire_boundary", False):
        try:
            fire_gdf = gpd.read_file(ROOT / cfg["fire_outline"])
            fire_feature = ShapelyFeature(fire_gdf.geometry, crs=pc)
            ax.add_feature(
                fire_feature,
                facecolor=cfg.get("fire_facecolor", "none"),
                edgecolor=cfg.get("fire_edgecolor", "0.3"),
                linewidth=cfg.get("fire_linewidth", 1.0),
                zorder=7
            )
        except Exception as e:
            print("Warning: fire boundary not drawn:", e)

    # --- Height contours (tricontour over safe triangulation) ---
    hmin, hmax = cfg["height_range"]
    hlev = np.arange(hmin, hmax, cfg["height_interval"])

    stride = int(cfg.get("tri_stride", 2))
    clip = bool(cfg.get("tri_clip_to_extent", True))
    max_edge = float(cfg.get("tri_max_edge_deg", 4.0))

    triZ, vZ = build_tri_safe(lon2, lat2, Z, extent, stride=stride, clip=clip, max_edge_deg=max_edge)

    ax.tricontour(triZ, vZ, levels=hlev, colors="black", linewidths=1.0, transform=pc, zorder=5)
    ax.tricontour(triZ, vZ, levels=cfg["height_highlight"], colors="black", linewidths=2.0, transform=pc, zorder=6)

    add_boxed_height_labels_rdps(ax, lon2, lat2, Z, cfg, pc, extent)

    # --- Vorticity contours ---
    triV, vV = build_tri_safe(lon2, lat2, V, extent, stride=stride, clip=clip, max_edge_deg=max_edge)

    ax.tricontour(
        triV, vV,
        levels=np.array(cfg["vort_levels"], dtype=float),
        colors="black",
        linewidths=cfg["vort_linewidth"],
        linestyles=cfg["vort_linestyle"],
        transform=pc,
        zorder=4
    )

    # --- H/L centres: plateau-pick + distance thinning (NO double-draw) ---
    if cfg.get("show_HL", True):
        win = int(cfg.get("hl_window", 51))

        inext = (
            (lon2 >= lon_min) & (lon2 <= lon_max) &
            (lat2 >= lat_min) & (lat2 <= lat_max) &
            np.isfinite(Z)
        )
        Zm = np.where(inext, Z, np.nan)

        Z_for_max = np.where(np.isfinite(Zm), Zm, -np.inf)
        Z_for_min = np.where(np.isfinite(Zm), Zm, +np.inf)

        zmax = maximum_filter(Z_for_max, size=win)
        zmin = minimum_filter(Z_for_min, size=win)

        is_hi = (Z_for_max == zmax) & np.isfinite(Zm)
        is_lo = (Z_for_min == zmin) & np.isfinite(Zm)

        hi_pts = pick_one_per_component(is_hi, Z, prefer="centroid")
        lo_pts = pick_one_per_component(is_lo, Z, prefer="centroid")

        hi_pts_ll = [(y, x, val, float(lat2[y, x]), float(lon2[y, x])) for y, x, val in hi_pts]
        lo_pts_ll = [(y, x, val, float(lat2[y, x]), float(lon2[y, x])) for y, x, val in lo_pts]

        min_deg = float(cfg.get("hl_deg_min_dist", 2.0))
        hi_pts_ll = thin_by_distance_latlon(hi_pts_ll, min_deg=min_deg, prefer="high")
        lo_pts_ll = thin_by_distance_latlon(lo_pts_ll, min_deg=min_deg, prefer="low")

        for y, x, val, lat, lon in hi_pts_ll:
            draw_HL(ax, lon, lat, "H", val, pc, lon_min, lon_max, lat_min, lat_max, cfg)

        for y, x, val, lat, lon in lo_pts_ll:
            draw_HL(ax, lon, lat, "L", val, pc, lon_min, lon_max, lat_min, lat_max, cfg)

    # --- Vort symbols (+/-) ---
    if cfg.get("show_vort_symbols", True):
        winv = int(cfg.get("vort_window", 39))

        inext_v = (
            (lon2 >= lon_min) & (lon2 <= lon_max) &
            (lat2 >= lat_min) & (lat2 <= lat_max) &
            np.isfinite(V)
        )
        Vm = np.where(inext_v, V, np.nan)

        thresh = float(cfg.get("vort_threshold", 0.0))
        label_pos_only = bool(cfg.get("vort_label_positive_only", False))

        V_for_max = np.where(np.isfinite(Vm), Vm, -np.inf)
        vmax = maximum_filter(V_for_max, size=winv)
        is_pos = (V_for_max == vmax) & (V_for_max > thresh)

        iy, ix = np.where(is_pos)
        # grid thinning here is fine; we don't have plateau overlap issues as much as H/L
        kept = []
        min_dist = int(cfg.get("vort_grid_min_dist", 10))
        for j in range(len(iy)):
            y, x = int(iy[j]), int(ix[j])
            ok = True
            for kk in kept:
                dy = y - int(iy[kk])
                dx = x - int(ix[kk])
                if (dy * dy + dx * dx) < (min_dist * min_dist):
                    ok = False
                    break
            if ok:
                kept.append(j)

        for j in kept:
            y, x = int(iy[j]), int(ix[j])
            lon = float(lon2[y, x]); lat = float(lat2[y, x]); val = float(V[y, x])
            draw_vort_symbol(ax, lon, lat, "+", val, pc, lon_min, lon_max, lat_min, lat_max, cfg)

        if not label_pos_only:
            V_for_min = np.where(np.isfinite(Vm), Vm, +np.inf)
            vmin = minimum_filter(V_for_min, size=winv)
            is_neg = (V_for_min == vmin) & (V_for_min < -thresh)

            iy, ix = np.where(is_neg)
            kept = []
            for j in range(len(iy)):
                y, x = int(iy[j]), int(ix[j])
                ok = True
                for kk in kept:
                    dy = y - int(iy[kk])
                    dx = x - int(ix[kk])
                    if (dy * dy + dx * dx) < (min_dist * min_dist):
                        ok = False
                        break
                if ok:
                    kept.append(j)

            for j in kept:
                y, x = int(iy[j]), int(ix[j])
                lon = float(lon2[y, x]); lat = float(lat2[y, x]); val = float(V[y, x])
                draw_vort_symbol(ax, lon, lat, "–", val, pc, lon_min, lon_max, lat_min, lat_max, cfg)

    # Save only if standalone
    if standalone:
        outpath = OUTDIR / cfg["output_filename"]
        fig.savefig(outpath, dpi=cfg["dpi"])
        print("Saved:", outpath)

    return ax


if __name__ == "__main__":
    plot_500hpa()
