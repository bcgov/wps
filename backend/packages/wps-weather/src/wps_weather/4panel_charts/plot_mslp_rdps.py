# -*- coding: utf-8 -*-
"""
RDPS MSLP + 1000–500 hPa Thickness (dam)

Supports:
- Standalone mode (creates fig/ax and saves PNG)
- Multi-panel mode (draws onto provided ax)

Requires:
- cfgrib + eccodes
"""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib as mpl
import matplotlib.patheffects as PathEffects

import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.feature import NaturalEarthFeature, ShapelyFeature

from scipy.ndimage import maximum_filter, minimum_filter, gaussian_filter
import geopandas as gpd
import matplotlib.patches as mpatches

# --------------------------------------------------
# CONFIG (RDPS)
# --------------------------------------------------
CFG_MSLP_RDPS = {
    # --- Input files ---
    # RDPS file name examples:
    # 20260106T06Z_MSC_RDPS_Pressure_MSL_RLatLon0.09_PT003H.grib2
    # 20260106T06Z_MSC_RDPS_Thickness_IsbL-1000to0500_RLatLon0.09_PT003H.grib2
    "mslp_grib": "data_hpfx/20260112/12/003/20260112T12Z_MSC_RDPS_Pressure_MSL_RLatLon0.09_PT003H.grib2",
    "thk_grib": "data_hpfx/20260112/12/003/20260112T12Z_MSC_RDPS_Thickness_IsbL-1000to0500_RLatLon0.09_PT003H.grib2",
    "fire_outline": "fire_centers_all.geojson",

    # --- Projection / domain ---
    "central_longitude": -130.0,
    "central_latitude": 50.0,
    "extent": [-160.0, -100.0, 30.0, 70.0],

    # --- Gridlines / labels ---
    "grid_dx": 10,
    "grid_dy": 10,
    "lon_label_value": -140,
    "lat_label_value": 40,
    "label_fontsize": 7,
    "label_alpha": 0.65,

    # --- Base map / fire boundary ---
    "show_fire_boundary": False,
    "fire_facecolor": "none",
    "fire_edgecolor": "0.3",
    "fire_linewidth": 0.4,
    "coastline_lw": 0.5,
    "borders_lw": 0.4,
    "province_lw": 0.5,

    # --- MSLP contours (hPa) ---
    "mslp_levels": list(np.arange(960, 1050, 4)),
    "mslp_linewidth": 1.0,
    "mslp_highlight_levels": [1000, 1024],
    "mslp_highlight_linewidth": 2.0,

    # ECCC-style boxed MSLP labels along one lon (RDPS-approx)
    "mslp_label_lon": -140.0,
    "mslp_label_tol": 3.0,
    "mslp_label_min_dlat": 0.7,
    "mslp_label_fontsize": 8,
    "label_lon_tol_deg": 0.35,  # how wide the "stripe" is around label lon

    # --- Thickness (dam) ---
    "thk_levels": list(np.arange(480, 600, 6)),
    "thk_linewidth": 1.0,
    "thk_linestyle": "dashed",

    # Shaded thickness band (hatch)
    "shade_band": True,
    "shade_min": 534,
    "shade_max": 540,
    "shade_hatch": ".....",
    "shade_hatch_linewidth": 0.15,

    # Boxed thickness labels along one lon (RDPS-approx)
    "thk_label_lon": -110.0,
    "thk_label_tol": 3.0,
    "thk_label_min_dlat": 0.7,
    "thk_label_fontsize": 8,

    # --- H/L detection based on MSLP ---
    "show_HL": True,
    "hl_window":  57,
    "hl_grid_min_dist": 50,  
    "hl_deg_min_dist": 5,

    # H/L drawing geometry and styles
    "hl_d_letter": 1.5,
    "hl_d_value": 1.2,
    "hl_pad_lon": 1.0,
    "hl_pad_lat": 1.0,
    "hl_letter_fontsize": 20,
    "hl_letter_halo_width": 3.0,
    "hl_center_fontsize": 10,
    "hl_center_halo_width": 2.0,
    "hl_value_fontsize": 10,
    "hl_value_halo_width": 2.0,

    # --- Smoothing (optional) ---
    # Usually leave MSLP smooth off; thickness can tolerate a touch.
    "smooth_mslp_sigma": 0.0,
    "smooth_thk_sigma": 0.0,

    # --- tricontour control ---
    "tri_stride": 2,            # 1=full res (slow), 2–3 recommended
    "tri_clip_to_extent": False,  # True = fewer points (faster) but can show clipped hull; False looks cleaner

    # --- Figure/Output (standalone only) ---
    "title": "RDPS MSLP + 1000–500 hPa Thickness (dam)",
    "output_dir": "outputs",
    "output_filename": "RDPS_MSLP_Thickness.png",
    "dpi": 300,
    "figsize": (10, 7),
    "subplots_adjust": {"left": 0.03, "right": 0.97, "bottom": 0.03, "top": 0.93},
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



def thin_pts_grid(iy: np.ndarray, ix: np.ndarray, min_dist: int = 25):
    """Thin points by minimum distance in grid coordinates. Returns indices into (iy, ix)."""
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


def draw_HL(ax, lon, lat, letter, val, pc, lon_min, lon_max, lat_min, lat_max, cfg):
    d_letter = cfg["hl_d_letter"]
    d_value = cfg["hl_d_value"]
    pad_lon = cfg["hl_pad_lon"]
    pad_lat = cfg["hl_pad_lat"]

    lat_letter = lat + d_letter
    lat_value = lat - d_value

    if (
        (lon < lon_min + pad_lon) or (lon > lon_max - pad_lon) or
        (lat_letter > lat_max - pad_lat) or
        (lat_value < lat_min + pad_lat)
    ):
        return

    txt = ax.text(
        lon, lat_letter, letter,
        transform=pc, ha="center", va="center",
        fontsize=cfg["hl_letter_fontsize"], fontweight="bold",
        color="black", zorder=12,
    )
    txt.set_path_effects([
        PathEffects.Stroke(linewidth=cfg["hl_letter_halo_width"], foreground="white"),
        PathEffects.Normal()
    ])

    circ = ax.text(
        lon, lat, "⊗",
        transform=pc, ha="center", va="center",
        fontsize=cfg["hl_center_fontsize"],
        color="black", zorder=12,
    )
    circ.set_path_effects([
        PathEffects.Stroke(linewidth=cfg["hl_center_halo_width"], foreground="white"),
        PathEffects.Normal()
    ])

    num = ax.text(
        lon, lat_value, f"{int(val)}",
        transform=pc, ha="center", va="center",
        fontsize=cfg["hl_value_fontsize"], fontweight="bold",
        color="black", zorder=12,
    )
    num.set_path_effects([
        PathEffects.Stroke(linewidth=cfg["hl_value_halo_width"], foreground="white"),
        PathEffects.Normal()
    ])

def further_thin_latlon_points(points_yx, lon2, lat2, field2, min_deg=1.5, prefer_high=True):
    """
    Thin a list of (y,x) points by minimum geographic distance (degrees),
    using a simple lat/lon metric. Keeps strongest first.
    """
    pts = []
    for (y, x) in points_yx:
        lon = float(lon2[y, x])
        lat = float(lat2[y, x])
        val = float(field2[y, x])
        pts.append((val, y, x, lat, lon))

    # highs: keep largest first; lows: keep smallest first
    pts.sort(reverse=prefer_high, key=lambda t: t[0])

    kept = []
    kept_latlon = []
    for val, y, x, lat, lon in pts:
        too_close = False
        for klat, klon in kept_latlon:
            dlat = lat - klat
            dlon = (lon - klon) * np.cos(np.radians((lat + klat) / 2.0))
            if (dlat * dlat + dlon * dlon) < (min_deg * min_deg):
                too_close = True
                break
        if not too_close:
            kept.append((y, x))
            kept_latlon.append((lat, lon))

    return kept

def _tri_points(lon2, lat2, fld2, extent, stride=2, clip=True):
    """Prepare irregular points for tricontour / tricontourf."""
    lon_s = lon2[::stride, ::stride]
    lat_s = lat2[::stride, ::stride]
    v_s = fld2[::stride, ::stride]

    lon_min, lon_max, lat_min, lat_max = extent

    m = np.isfinite(v_s) & np.isfinite(lon_s) & np.isfinite(lat_s)
    if clip:
        m = (
            m &
            (lon_s >= lon_min) & (lon_s <= lon_max) &
            (lat_s >= lat_min) & (lat_s <= lat_max)
        )

    x = lon_s[m].ravel()
    y = lat_s[m].ravel()
    v = v_s[m].ravel()
    return x, y, v



def _boxed_labels_along_lon_rdps(ax, lon2, lat2, field2, levels, cfg,
                                lon_target, tol_val, min_dlat, fontsize, pc, extent,
                                text_color="white", facecolor="black", edgecolor="black",
                                lw=0.7, tol_lon=None):
    """
    RDPS-friendly 'boxed labels along one longitude':
    pick points close to lon_target, then for each level choose best match.
    """
    if tol_lon is None:
        tol_lon = float(cfg.get("label_lon_tol_deg", 0.35))
    lon_min, lon_max, lat_min, lat_max = extent

    m = (
        np.isfinite(field2) &
        np.isfinite(lon2) & np.isfinite(lat2) &
        (np.abs(lon2 - lon_target) <= tol_lon) &
        (lon2 >= lon_min) & (lon2 <= lon_max) &
        (lat2 >= lat_min) & (lat2 <= lat_max)
    )
    if not np.any(m):
        return

    cand_lon = lon2[m]
    cand_lat = lat2[m]
    cand_f = field2[m]

    used_lats = []
    for lev in levels:
        idx = int(np.argmin(np.abs(cand_f - lev)))
        if float(np.abs(cand_f[idx] - lev)) > float(tol_val):
            continue
        lat_lab = float(cand_lat[idx])
        if any(abs(lat_lab - u) < float(min_dlat) for u in used_lats):
            continue
        used_lats.append(lat_lab)

        ax.text(
            lon_target, lat_lab, f"{int(lev)}",
            transform=pc, ha="center", va="center",
            fontsize=fontsize,  fontweight="bold",color=text_color,
            bbox=dict(
                boxstyle="square,pad=0.1",
                facecolor=facecolor,
                edgecolor=edgecolor,
                linewidth=lw
            ),
            zorder=8
        )


# --------------------------------------------------
# Main plotter
# --------------------------------------------------
def plot_mslp_thickness_rdps(cfg=None, ax=None):
    if cfg is None:
        cfg = CFG_MSLP_RDPS

    ROOT = get_project_root()
    OUTDIR = ROOT / cfg["output_dir"]
    OUTDIR.mkdir(exist_ok=True)

    plt.rcParams["font.size"] = cfg.get("label_fontsize", 7)
    plt.rcParams["axes.linewidth"] = 0.3

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

    # --- Open data ---
    ds_msl = open_ds(ROOT / cfg["mslp_grib"])
    ds_thk = open_ds(ROOT / cfg["thk_grib"])

    msl = ds_msl[list(ds_msl.data_vars)[0]].squeeze()
    thk = ds_thk[list(ds_thk.data_vars)[0]].squeeze()

    # Coordinates (RDPS: 2D)
    lat2 = ds_msl["latitude"].values
    lon2 = ds_msl["longitude"].values

    # Units
    mslp = (msl / 100.0).astype(np.float64)  # Pa -> hPa

    thk_vals = thk.values
    thickness = (thk / 10.0) if float(np.nanmax(thk_vals)) > 1000 else thk
    thickness = thickness.astype(np.float64)  # dam

    Z = mslp.values.astype(np.float64)
    T = thickness.values.astype(np.float64)

    # Optional smoothing
    sZ = float(cfg.get("smooth_mslp_sigma", 0.0))
    sT = float(cfg.get("smooth_thk_sigma", 0.0))
    if sZ > 0:
        Z = gaussian_filter(Z, sigma=sZ)
    if sT > 0:
        T = gaussian_filter(T, sigma=sT)

    # --- Gridlines + single labels ---
    gl = ax.gridlines(draw_labels=False, crs=pc, color="black", linewidth=0.4,
                      alpha=0.4, linestyle="dotted")
    gl.xlocator = mticker.FixedLocator(np.arange(-180, 181, cfg["grid_dx"]))
    gl.ylocator = mticker.FixedLocator(np.arange(0, 91, cfg["grid_dy"]))

    ax.text(cfg["lon_label_value"], lat_max - 1.5, f"{abs(cfg['lon_label_value'])}W",
            transform=pc, fontsize=cfg["label_fontsize"], alpha=cfg["label_alpha"],
            ha="center", va="center")
    ax.text(lon_min + 1.5, cfg["lat_label_value"], f"{cfg['lat_label_value']}N",
            transform=pc, fontsize=cfg["label_fontsize"], alpha=cfg["label_alpha"],
            ha="center", va="center")

    # --- Base map features ---
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
                edgecolor=cfg["fire_edgecolor"],
                facecolor=cfg["fire_facecolor"],
                linewidth=cfg["fire_linewidth"],
                zorder=1,
            )
        except Exception as e:
            print("Warning: fire boundary not drawn:", e)

    # --- tricontour control ---
    stride = int(cfg.get("tri_stride", 2))
    clip = bool(cfg.get("tri_clip_to_extent", False))

    # --- MSLP contours ---
    msl_levels = np.array(cfg["mslp_levels"], dtype=float)
    xZ, yZ, vZ = _tri_points(lon2, lat2, Z, extent, stride=stride, clip=clip)

    ax.tricontour(
        xZ, yZ, vZ,
        levels=msl_levels,
        colors="black",
        linewidths=cfg["mslp_linewidth"],
        transform=pc, zorder=5
    )

    hlv = np.array(cfg.get("mslp_highlight_levels", []), dtype=float)
    if hlv.size > 0:
        ax.tricontour(
            xZ, yZ, vZ,
            levels=hlv,
            colors="black",
            linewidths=cfg["mslp_highlight_linewidth"],
            transform=pc, zorder=6
        )

    # Boxed MSLP labels along one longitude (RDPS approximation)
    _boxed_labels_along_lon_rdps(
        ax=ax, lon2=lon2, lat2=lat2, field2=Z,
        levels=msl_levels,
        cfg=cfg,
        lon_target=float(cfg["mslp_label_lon"]),
        tol_val=float(cfg["mslp_label_tol"]),
        min_dlat=float(cfg["mslp_label_min_dlat"]),
        fontsize=int(cfg["mslp_label_fontsize"]),
        pc=pc,
        extent=extent,
        text_color="white",
        facecolor="black",
        edgecolor="black",
        lw=0.7
    )

    # --- Thickness shaded band (hatched) + contours ---
    xT, yT, vT = _tri_points(lon2, lat2, T, extent, stride=stride, clip=clip)

    old_hlw = mpl.rcParams.get("hatch.linewidth", 1.0)
    if cfg.get("shade_band", True):
        mpl.rcParams["hatch.linewidth"] = cfg["shade_hatch_linewidth"]
        ax.tricontourf(
            xT, yT, vT,
            levels=[cfg["shade_min"], cfg["shade_max"]],
            colors="none",
            hatches=[cfg["shade_hatch"]],
            transform=pc,
            zorder=4
        )
    mpl.rcParams["hatch.linewidth"] = old_hlw

    thk_levels = np.array(cfg["thk_levels"], dtype=float)
    ax.tricontour(
        xT, yT, vT,
        levels=thk_levels,
        colors="black",
        linewidths=cfg["thk_linewidth"],
        linestyles=cfg["thk_linestyle"],
        transform=pc, zorder=7
    )

    # Boxed thickness labels along one longitude (RDPS approximation)
    _boxed_labels_along_lon_rdps(
        ax=ax, lon2=lon2, lat2=lat2, field2=T,
        levels=thk_levels,
        cfg=cfg,
        lon_target=float(cfg["thk_label_lon"]),
        tol_val=float(cfg["thk_label_tol"]),
        min_dlat=float(cfg["thk_label_min_dlat"]),
        fontsize=int(cfg["thk_label_fontsize"]),
        pc=pc,
        extent=extent,
        text_color="black",
        facecolor="white",
        edgecolor="black",
        lw=0.5
    )

    # --- H/L centres from MSLP field (grid-space extrema + thinning) ---
    if cfg.get("show_HL", True):
        win = int(cfg.get("hl_window", 57))

        # Restrict extrema search to points inside extent (prevents junk labels)
        inext = (
            (lon2 >= lon_min) & (lon2 <= lon_max) &
            (lat2 >= lat_min) & (lat2 <= lat_max) &
            np.isfinite(Z)
        )
        Zm = np.where(inext, Z, np.nan)

        # Filters don't like NaNs; use +/-inf outside region
        Z_for_max = np.where(np.isfinite(Zm), Zm, -np.inf)
        Z_for_min = np.where(np.isfinite(Zm), Zm, +np.inf)

        zmax = maximum_filter(Z_for_max, size=win)
        zmin = minimum_filter(Z_for_min, size=win)

        hi = np.where((Z_for_max == zmax) & np.isfinite(Zm))
        lo = np.where((Z_for_min == zmin) & np.isfinite(Zm))

        hi_k = thin_pts_grid(hi[0], hi[1], min_dist=int(cfg.get("hl_grid_min_dist", 25)))
        lo_k = thin_pts_grid(lo[0], lo[1], min_dist=int(cfg.get("hl_grid_min_dist", 25)))
        
        # Convert grid-thinned indices -> (y,x) lists
        hi_pts = [(int(hi[0][j]), int(hi[1][j])) for j in hi_k]
        lo_pts = [(int(lo[0][j]), int(lo[1][j])) for j in lo_k]
        
        # Extra thinning in geographic space (prevents duplicate H/L like your bottom-left)
        min_deg = float(cfg.get("hl_deg_min_dist", 2.0))
        hi_final = further_thin_latlon_points(hi_pts, lon2, lat2, Z, min_deg=min_deg, prefer_high=True)
        lo_final = further_thin_latlon_points(lo_pts, lon2, lat2, Z, min_deg=min_deg, prefer_high=True)

        for y, x in hi_final:
            lon = float(lon2[y, x]); lat = float(lat2[y, x]); val = float(Z[y, x])
            draw_HL(ax, lon, lat, "H", val, pc, lon_min, lon_max, lat_min, lat_max, cfg)
        
        for y, x in lo_final:
            lon = float(lon2[y, x]); lat = float(lat2[y, x]); val = float(Z[y, x])
            draw_HL(ax, lon, lat, "L", val, pc, lon_min, lon_max, lat_min, lat_max, cfg)
    
    # --- Legend for hatched thickness band --- 
    old_hlw = mpl.rcParams["hatch.linewidth"]
    mpl.rcParams["hatch.linewidth"] = cfg["shade_hatch_linewidth"]    
    legend_elements = []

    if cfg["shade_band"]:
        legend_elements.append(
            mpatches.Patch(
                facecolor="white",
                hatch=cfg["shade_hatch"],
                edgecolor='black',
                label=r"$534 \leq \Delta Z \leq 540$ dam"
                )
            )
    
    leg = ax.legend(
        handles=legend_elements,
        loc="lower right",
        fontsize=7,
        frameon=True,
        handleheight=1.8
        )
        
    mpl.rcParams["hatch.linewidth"] = old_hlw
    leg.set_zorder(100)  # draw legend on top of everything
    # --- FORCE white background ---
    frame = leg.get_frame()
    frame.set_facecolor("white")
    frame.set_edgecolor("black")
    frame.set_alpha(1.0)
    
    # --- IMPORTANT for Cartopy ---
    leg.set_clip_on(False)

    # Titles / output
    if standalone:
        ax.set_title(cfg["title"], fontsize=10)
        plt.subplots_adjust(**cfg["subplots_adjust"])
        out_path = OUTDIR / cfg["output_filename"]
        fig.savefig(out_path, dpi=cfg["dpi"])
        print("Saved:", out_path)
    else:
        ax.set_title("")

    return ax


if __name__ == "__main__":
    plot_mslp_thickness_rdps()
