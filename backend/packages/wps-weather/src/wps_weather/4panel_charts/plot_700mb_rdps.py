# -*- coding: utf-8 -*-
"""
RDPS 700 hPa Height (dam) + 850–700–500 hPa Layer-Mean RH (%)

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
import matplotlib as mpl
import matplotlib.patheffects as PathEffects

import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.feature import NaturalEarthFeature, ShapelyFeature

from scipy.ndimage import maximum_filter, minimum_filter, gaussian_filter
import geopandas as gpd
import matplotlib.patches as mpatches
import matplotlib.tri as mtri
from matplotlib.patches import Patch
# --------------------------------------------------
# CONFIG (RDPS)
# --------------------------------------------------
CFG_700_RDPS = {
    # =====  Height file  =====
    "z700_grib": "data_hpfx/20260109/12/006/20260109T12Z_MSC_RDPS_GeopotentialHeight_IsbL-0700_RLatLon0.09_PT006H.grib2",
    # =====  Three RH files (for layer-mean)  =====
    "rh850_grib": "data_hpfx/20260109/12/006/20260109T12Z_MSC_RDPS_RelativeHumidity_IsbL-0850_RLatLon0.09_PT006H.grib2",

    "rh700_grib": "data_hpfx/20260109/12/006/20260109T12Z_MSC_RDPS_RelativeHumidity_IsbL-0700_RLatLon0.09_PT006H.grib2",
    "rh700_index": "rh700_rdps.idx",

    "rh500_grib": "data_hpfx/20260109/12/006/20260109T12Z_MSC_RDPS_RelativeHumidity_IsbL-0500_RLatLon0.09_PT006H.grib2",
    "rh500_index": "rh500_rdps.idx",

    # --- Fire boundary (optional) ---
    "fire_outline": "fire_centers_all.geojson",
    "show_fire_boundary": False,
    "fire_facecolor": "none",
    "fire_edgecolor": "0.3",
    "fire_linewidth": 0.4,

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

    # --- Basemap styling ---
    "coastline_lw": 0.5,
    "borders_lw": 0.4,
    "province_lw": 0.5,

    # --- 700 hPa heights (dam) ---
    "height_interval": 6,
    "height_range": [240, 330],
    "height_highlight": [276, 300],  # bold

    # Black boxed height labels
    "height_label_levels": list(np.arange(264, 320, 6)),
    "height_label_lon": -140.0,
    "height_label_tol": 3.0,
    "height_label_min_dlat": 0.7,

    # --- Humidity contours ---
    "rh_levels": [50, 70, 90],
    "rh_linewidth": 1.0,
    "rh_linestyle": "dashed",

    # White boxed RH labels at multiple longitudes
    "rh_label_levels": [50, 70, 90],
    "rh_label_lons": [-165.0, -160.0, -150.0, -145.0, -130.0, -115.0, -100.0],
    "rh_label_tol": 2.0,
    "rh_label_min_dlat": 0.7,

    # --- Shaded humidity bands (dots) ---
    "shade_70_90": True,
    "shade_90_plus": True,
    "shade_70_90_hatch": "....",
    "shade_90_plus_hatch": ".......",
    "shade_hatch_lw": 0.15,
    "shade_edge_lw": 0.6,
    "shade_hatch_lw": 0.15,
    "shade_70_color": "#d9d9d9",   # Humidity 70% area color Light grey (light blue #bcd9ff). 
    "shade_90_color": "#6b6b6b",   # Humidity 90% area color Dark grey (dark blue #1f5fa8).  

    # --- H/L centres based on 700-hPa height ---
    "show_HL": True,
    "hl_window": 41,
    "hl_grid_min_dist": 25,   # 
    "hl_deg_min_dist": 5.0,   # extra thinning in geographic space

    # H/L drawing geometry and styles
    "hl_d_letter": 1.5,
    "hl_d_value": 1.2,
    "hl_pad_lon": 1.0,
    "hl_pad_lat": 1.0,
    "hl_letter_fontsize": 22,
    "hl_letter_halo_width": 3.0,
    "hl_center_fontsize": 10,
    "hl_center_halo_width": 2.0,
    "hl_value_fontsize": 10,
    "hl_value_halo_width": 2.0,

    # --- Smoothing (optional; usually keep light) ---
    "smooth_height_sigma": 0.0,   # try 0.0 or 0.4
    "smooth_rh_sigma": 0.6,       # try 0.4–1.0

    # --- Triangulation control (projected tricontour) ---
    "tri_stride": 2,                 # 1=full res (slow), 2–3 recommended
    "tri_clip_to_extent": False,      # True recommended with PAD below
    "tri_clip_pad_deg": 5.0,         # KEY: pad extent so hull doesn't cut into plot

    # --- Output ---
    "title": "RDPS 700 hPa Height (dam) + 850–700–500 hPa Humidity (%)",
    "output_dir": "outputs",
    "output_filename": "RDPS_700hPa_Height_Humidity.png",
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


def further_thin_latlon_points(points_yx, lon2, lat2, field2, min_deg=2.0, prefer_high=True):
    pts = []
    for (y, x) in points_yx:
        lon = float(lon2[y, x])
        lat = float(lat2[y, x])
        val = float(field2[y, x])
        pts.append((val, y, x, lat, lon))

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
        color="black", zorder=20,
    )
    txt.set_path_effects([
        PathEffects.Stroke(linewidth=cfg["hl_letter_halo_width"], foreground="white"),
        PathEffects.Normal()
    ])

    circ = ax.text(
        lon, lat, "⊗",
        transform=pc, ha="center", va="center",
        fontsize=cfg["hl_center_fontsize"],
        color="black", zorder=20,
    )
    circ.set_path_effects([
        PathEffects.Stroke(linewidth=cfg["hl_center_halo_width"], foreground="white"),
        PathEffects.Normal()
    ])

    num = ax.text(
        lon, lat_value, f"{int(val)}",
        transform=pc, ha="center", va="center",
        fontsize=cfg["hl_value_fontsize"], fontweight="bold",
        color="black", zorder=20,
    )
    num.set_path_effects([
        PathEffects.Stroke(linewidth=cfg["hl_value_halo_width"], foreground="white"),
        PathEffects.Normal()
    ])


def _tri_points_projected(lon2, lat2, fld2, extent, proj, pc, stride=2, clip=True, pad_deg=5.0):
    """
    Build 1D arrays (x, y, v) for tricontour where x/y are in *projected* coordinates.
    This avoids RDPS "wedge" / scope artifacts.

    clip=True will keep only points in an expanded (padded) lat/lon extent.
    """
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

    # project lon/lat -> x/y in the target axes projection
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
def _boxed_labels_along_lon_rdps(ax, lon2, lat2, field2, levels, cfg,
                                lon_target, tol_val, min_dlat, fontsize, pc, extent,
                                text_color="white", facecolor="black", edgecolor="black",
                                lw=0.7, tol_lon=0.35):
    """
    RDPS-friendly boxed labels along a longitude stripe.
    """
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
            fontsize=fontsize, fontweight="bold", color=text_color,
            bbox=dict(
                boxstyle="square,pad=0.1",
                facecolor=facecolor,
                edgecolor=edgecolor,
                linewidth=lw
            ),
            zorder=18
        )


# --------------------------------------------------
# Main plotter
# --------------------------------------------------
def plot_700hpa_rdps(cfg=None, ax=None):
    if cfg is None:
        cfg = CFG_700_RDPS

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

    # --------------------------------------------------
    # 1) Load height + RHs
    # --------------------------------------------------
    ds_z700 = open_ds(ROOT / cfg["z700_grib"])
    z700 = ds_z700[list(ds_z700.data_vars)[0]].squeeze()

    H700 = z700 / 10.0 if float(z700.max()) > 1000 else z700
    Z = H700.values.astype(np.float64)

    ds_rh850 = open_ds(ROOT / cfg["rh850_grib"])
    ds_rh700 = open_ds(ROOT / cfg["rh700_grib"])
    ds_rh500 = open_ds(ROOT / cfg["rh500_grib"])

    rh850 = ds_rh850[list(ds_rh850.data_vars)[0]].squeeze()
    rh700 = ds_rh700[list(ds_rh700.data_vars)[0]].squeeze()
    rh500 = ds_rh500[list(ds_rh500.data_vars)[0]].squeeze()

    RH = ((rh850 + rh700 + rh500) / 3.0).astype(np.float64)
    RHv = RH.values.astype(np.float64)

    # RDPS: 2D coords
    lat2 = ds_z700["latitude"].values
    lon2 = ds_z700["longitude"].values

    # Optional smoothing
    sigZ = float(cfg.get("smooth_height_sigma", 0.0))
    sigR = float(cfg.get("smooth_rh_sigma", 0.0))
    if sigZ > 0:
        Z = gaussian_filter(Z, sigma=sigZ)
    if sigR > 0:
        RHv = gaussian_filter(RHv, sigma=sigR)

    # --------------------------------------------------
    # 2) Gridlines + single labels
    # --------------------------------------------------
    gl = ax.gridlines(draw_labels=False, crs=pc, color="black",
                      linewidth=0.4, alpha=0.4, linestyle="dotted")
    gl.xlocator = mticker.FixedLocator(np.arange(-180, 181, cfg["grid_dx"]))
    gl.ylocator = mticker.FixedLocator(np.arange(0, 91, cfg["grid_dy"]))

    ax.text(cfg["lon_label_value"], lat_max - 1.5, f"{abs(cfg['lon_label_value'])}W",
            transform=pc, fontsize=cfg["label_fontsize"], alpha=cfg["label_alpha"],
            ha="center", va="center")
    ax.text(lon_min + 1.5, cfg["lat_label_value"], f"{cfg['lat_label_value']}N",
            transform=pc, fontsize=cfg["label_fontsize"], alpha=cfg["label_alpha"],
            ha="center", va="center")

    # --------------------------------------------------
    # 3) Base map
    # --------------------------------------------------
    ax.add_feature(cfeature.LAND, facecolor="white", edgecolor="black", linewidth=0.4, zorder=0)
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
                linewidth=cfg.get("fire_linewidth", 0.4),
                zorder=1,
            )
        except Exception as e:
            print("Warning: fire boundary not drawn:", e)

    # --------------------------------------------------
    # 4) Prepare projected tri points (THIS FIXES SCOPE)
    # --------------------------------------------------
    stride = int(cfg.get("tri_stride", 2))
    clip = bool(cfg.get("tri_clip_to_extent", True))
    pad_deg = float(cfg.get("tri_clip_pad_deg", 5.0))

    xZ, yZ, vZ = _tri_points_projected(lon2, lat2, Z, extent, proj, pc,
                                       stride=stride, clip=clip, pad_deg=pad_deg)
    xR, yR, vR = _tri_points_projected(lon2, lat2, RHv, extent, proj, pc,
                                       stride=stride, clip=clip, pad_deg=pad_deg)

    # --------------------------------------------------
    # 5) Height contours (projected tricontour, NO transform=)
    # --------------------------------------------------
    hmin, hmax = cfg["height_range"]
    hlev = np.arange(hmin, hmax + cfg["height_interval"], cfg["height_interval"])

    ax.tricontour(xZ, yZ, vZ, levels=hlev, colors="black", linewidths=1.0, zorder=5)
    ax.tricontour(xZ, yZ, vZ, levels=cfg["height_highlight"], colors="black", linewidths=2.0, zorder=6)

    # black boxed height labels along one longitude (RDPS stripe)
    _boxed_labels_along_lon_rdps(
        ax=ax, lon2=lon2, lat2=lat2, field2=Z,
        levels=np.array(cfg["height_label_levels"], dtype=float),
        cfg=cfg,
        lon_target=float(cfg["height_label_lon"]),
        tol_val=float(cfg["height_label_tol"]),
        min_dlat=float(cfg["height_label_min_dlat"]),
        fontsize=8,
        pc=pc,
        extent=extent,
        text_color="white",
        facecolor="black",
        edgecolor="black",
        lw=0.7,
        tol_lon=0.35
    )

    # --------------------------------------------------
    # 6) RH shading + contours + boxed labels (projected tricontourf)
    # --------------------------------------------------
    old_hlw = mpl.rcParams.get("hatch.linewidth", 1.0)
    mpl.rcParams["hatch.linewidth"] = cfg["shade_hatch_lw"]

    if cfg.get("shade_70_90", True):
        ax.tricontourf(
            xR, yR, vR,
            levels=[70, 90],
            colors=[cfg["shade_70_color"]],
            hatches=[cfg["shade_70_90_hatch"]],
            zorder=3
        )

    if cfg.get("shade_90_plus", True):
        ax.tricontourf(
            xR, yR, vR,
            levels=[90, 100],
            colors=[cfg["shade_90_color"]],
            hatches=[cfg["shade_90_plus_hatch"]],
            zorder=4
        )

    mpl.rcParams["hatch.linewidth"] = old_hlw

    ax.tricontour(
        xR, yR, vR,
        levels=np.array(cfg["rh_levels"], dtype=float),
        colors="black",
        linewidths=cfg["rh_linewidth"],
        linestyles=cfg["rh_linestyle"],
        zorder=8
    )

    # White boxed RH labels at multiple longitudes (RDPS stripe)
    # for lon_lab in cfg["rh_label_lons"]:
    #     _boxed_labels_along_lon_rdps(
    #         ax=ax, lon2=lon2, lat2=lat2, field2=RHv,
    #         levels=np.array(cfg["rh_label_levels"], dtype=float),
    #         cfg=cfg,
    #         lon_target=float(lon_lab),
    #         tol_val=float(cfg["rh_label_tol"]),
    #         min_dlat=float(cfg["rh_label_min_dlat"]),
    #         fontsize=6,
    #         pc=pc,
    #         extent=extent,
    #         text_color="black",
    #         facecolor="white",
    #         edgecolor="black",
    #         lw=0.7,
    #         tol_lon=0.35
    #     )

    # --------------------------------------------------
    # 7) H/L centres on 700 hPa height
    # --------------------------------------------------
    if cfg.get("show_HL", True):
        win = int(cfg.get("hl_window", 41))

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

        hi = np.where((Z_for_max == zmax) & np.isfinite(Zm))
        lo = np.where((Z_for_min == zmin) & np.isfinite(Zm))

        hi_k = thin_pts_grid(hi[0], hi[1], min_dist=int(cfg.get("hl_grid_min_dist", 50)))
        lo_k = thin_pts_grid(lo[0], lo[1], min_dist=int(cfg.get("hl_grid_min_dist", 50)))

        hi_pts = [(int(hi[0][j]), int(hi[1][j])) for j in hi_k]
        lo_pts = [(int(lo[0][j]), int(lo[1][j])) for j in lo_k]

        min_deg = float(cfg.get("hl_deg_min_dist", 2.0))
        hi_final = further_thin_latlon_points(hi_pts, lon2, lat2, Z, min_deg=min_deg, prefer_high=True)
        lo_final = further_thin_latlon_points(lo_pts, lon2, lat2, Z, min_deg=min_deg, prefer_high=False)

        for y, x in hi_final:
            lon = float(lon2[y, x]); lat = float(lat2[y, x]); val = float(Z[y, x])
            draw_HL(ax, lon, lat, "H", val, pc, lon_min, lon_max, lat_min, lat_max, cfg)

        for y, x in lo_final:
            lon = float(lon2[y, x]); lat = float(lat2[y, x]); val = float(Z[y, x])
            draw_HL(ax, lon, lat, "L", val, pc, lon_min, lon_max, lat_min, lat_max, cfg)
    # --------------------------------------------------
    # 8) Add RH legend for humidity bands
    # --------------------------------------------------       
    
    old_hlw = mpl.rcParams["hatch.linewidth"]
    mpl.rcParams["hatch.linewidth"] = cfg["shade_hatch_lw"]    
    legend_elements = []
    
    # # 50–70% RH (contours only)
    # legend_elements.append(
    #     Patch(
    #         facecolor="white",
    #         edgecolor="black",
    #         linestyle=cfg["rh_linestyle"],  # dashed
    #         linewidth=cfg["rh_linewidth"],
    #         label="RH 50–70%"
    #         )
    #     )

    if cfg["shade_70_90"]:
        legend_elements.append(
            Patch(
                facecolor=cfg["shade_70_color"],
                hatch=cfg["shade_70_90_hatch"],
                edgecolor='black',
                label='RH 70–90%'
            )
        )

    if cfg["shade_90_plus"]:
        legend_elements.append(
            Patch(
                facecolor=cfg["shade_90_color"],
                hatch=cfg["shade_90_plus_hatch"],
                edgecolor='black',
                label='RH > 90%'
            )
        )
        
        # Add legend to the axes
        leg = ax.legend( 
            handles=legend_elements,
            loc='upper right',    # choose location
            #bbox_to_anchor=(1.0, 1.0), 
            #borderaxespad=0.0,
            fontsize=7,
            ncol=1,
            frameon=True,
            facecolor='white',
            edgecolor='black', 
            framealpha=1.0,
            handleheight=1.8
        )
        mpl.rcParams["hatch.linewidth"] = old_hlw
        leg.set_zorder(100)  # draw legend on top of everything
    # --------------------------------------------------
    # Title / output
    # --------------------------------------------------
    if standalone:
        ax.set_title(cfg["title"], fontsize=10)
        plt.subplots_adjust(**cfg.get("subplots_adjust", {}))
        out_path = OUTDIR / cfg["output_filename"]
        fig.savefig(out_path, dpi=cfg["dpi"])
        print("Saved:", out_path)
    else:
        ax.set_title("")

    return ax


if __name__ == "__main__":
    plot_700hpa_rdps()
