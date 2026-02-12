# -*- coding: utf-8 -*-
"""
GDPS 700 hPa Height + Layer-Mean Humidity (850–700–500)

Supports:
- Standalone mode: plot_700hpa() -> creates fig/ax and saves PNG
- Multi-panel mode: plot_700hpa(ax=existing_ax) -> draws on given ax, no save
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
from matplotlib.patches import Patch


# --------------------------------------------------
# FINAL "decided" feature values live here
# --------------------------------------------------
CFG_700 = {
    # =====  Height file  =====
    "z700_grib": "data/20251121T12Z_MSC_GDPS_GeopotentialHeight_IsbL-0700_LatLon0.15_PT000H.grib2",
    "z700_index": "z700.idx",

    # =====  Three RH files (for layer-mean)  =====
    "rh850_grib": "data/20251121T12Z_MSC_GDPS_RelativeHumidity_IsbL-0850_LatLon0.15_PT000H.grib2",
    "rh850_index": "rh850.idx",

    "rh700_grib": "data/20251121T12Z_MSC_GDPS_RelativeHumidity_IsbL-0700_LatLon0.15_PT000H.grib2",
    "rh700_index": "rh700.idx",

    "rh500_grib": "data/20251121T12Z_MSC_GDPS_RelativeHumidity_IsbL-0500_LatLon0.15_PT000H.grib2",
    "rh500_index": "rh500.idx",

    # --- Fire boundary (optional) ---
    "fire_outline": "fire_centers_all.geojson",
    "show_fire_boundary": False,
    "fire_facecolor": "none",
    "fire_edgecolor": "0.3",
    "fire_linewidth": 1.0,

    # --- Domain / projection ---
    "central_longitude": -130.0,
    "central_latitude": 50.0,
    "extent": [-170.0, -100.0, 30.0, 75.0],

    # --- Gridlines / labels ---
    "grid_dx": 10,
    "grid_dy": 10,
    "lon_label_value": -140,
    "lat_label_value": 40,

    # --- 700 hPa heights ---
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
    "shade_70_90_hatch": "....",       # lighter dots
    "shade_90_plus_hatch": ".......",   # denser dots
    "shade_edge_lw": 0.6,
    "shade_hatch_lw": 0.15,
    "shade_70_color": "#d9d9d9",   # Humidity 70% area color Light grey (light blue #bcd9ff). 
    "shade_90_color": "#6b6b6b",   # Humidity 90% area color Dark grey (dark blue #1f5fa8).  

    # --- H/L centres based on 700-hPa height ---
    "show_HL": True,
    "hl_window": 41,
    "hl_grid_min_dist": 25,
    "hl_deg_min_dist": 5,
    "hl_d_letter": 1.5,
    "hl_d_value": 1.2,
    "hl_pad_lon": 1.0,
    "hl_pad_lat": 1.0,
    "hl_letter_fontsize": 22,
    "hl_center_fontsize": 10,
    "hl_value_fontsize": 10,

    # --- Styling / figure (standalone) ---
    "figsize": (10, 7),
    "dpi": 300,
    "title": "GDPS 700 hPa Height (dam) + 850–700–500 hPa Humidity (%)",
    "base_fontsize": 7,
    "axes_linewidth": 0.3,

    # --- Output (standalone) ---
    "output_dir": "outputs",
    "output_filename": "GDPS_700hPa_Height_Humidity.png",
    "tight_layout_pad": 0.2,
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
        too_close = False
        for klat, klon in kept_latlon:
            dlat = lat - klat
            dlon = (lon - klon) * np.cos(np.radians((lat + klat) / 2.0))
            if (dlat*dlat + dlon*dlon) < min_deg**2:
                too_close = True
                break
        if not too_close:
            kept.append((iy_s, ix_s))
            kept_latlon.append((lat, lon))
    return kept


def draw_HL(ax, lon, lat, letter, val, pc,
            lon_min, lon_max, lat_min, lat_max, cfg):
    d_letter = cfg["hl_d_letter"]
    d_value  = cfg["hl_d_value"]
    pad_lon  = cfg["hl_pad_lon"]
    pad_lat  = cfg["hl_pad_lat"]

    lat_letter = lat + d_letter
    lat_value  = lat - d_value

    if (
        lon < lon_min + pad_lon or lon > lon_max - pad_lon or
        lat_letter > lat_max - pad_lat or lat_value < lat_min + pad_lat
    ):
        return

    txt = ax.text(
        lon, lat_letter, letter,
        transform=pc,
        ha="center", va="center",
        fontsize=cfg["hl_letter_fontsize"], fontweight="bold",
        color="black", zorder=20,
    )
    txt.set_path_effects([
        PathEffects.Stroke(linewidth=3, foreground="white"),
        PathEffects.Normal()
    ])

    circ = ax.text(
        lon, lat, "⊗",
        transform=pc,
        ha="center", va="center",
        fontsize=cfg["hl_center_fontsize"],
        color="black", zorder=20,
    )
    circ.set_path_effects([
        PathEffects.Stroke(linewidth=2, foreground="white"),
        PathEffects.Normal()
    ])

    num = ax.text(
        lon, lat_value, f"{int(val)}",
        transform=pc,
        ha="center", va="center",
        fontsize=cfg["hl_value_fontsize"], fontweight="bold",
        color="black", zorder=20,
    )
    num.set_path_effects([
        PathEffects.Stroke(linewidth=2, foreground="white"),
        PathEffects.Normal()
    ])


def add_column_labels(ax, lon_plot, lats, field2d,
                      lon_label, lat_min, lat_max,
                      levels, tol, min_dlat,
                      pc, text_kwargs, bbox_kwargs):
    idx_lon = int(np.argmin(np.abs(lon_plot - lon_label)))

    lat_mask = (lats >= lat_min) & (lats <= lat_max)
    lats_sub = lats[lat_mask]
    col = field2d[:, idx_lon][lat_mask]

    used_lats = []
    for lev in levels:
        if col.size == 0:
            continue
        iy = int(np.argmin(np.abs(col - lev)))
        if float(abs(col[iy] - lev)) > tol:
            continue

        lat_lab = float(lats_sub[iy])
        if any(abs(lat_lab - ul) < min_dlat for ul in used_lats):
            continue
        used_lats.append(lat_lab)

        ax.text(
            lon_label, lat_lab, f"{int(lev)}",
            transform=pc,
            ha="center", va="center",
            bbox=bbox_kwargs,
            zorder=18,
            **text_kwargs,
        )


# --------------------------------------------------
# Main plotter
# --------------------------------------------------
def plot_700hpa(cfg=None, ax=None):
    if cfg is None:
        cfg = CFG_700
    ROOT = get_project_root()
    OUTDIR = ROOT / cfg["output_dir"]
    OUTDIR.mkdir(exist_ok=True)

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

    lon_min, lon_max, lat_min, lat_max = cfg["extent"]
    ax.set_extent(cfg["extent"], crs=pc)

    # --------------------------------------------------
    # 1) Load height + RHs
    # --------------------------------------------------
    ds_z700 = open_ds(ROOT / cfg["z700_grib"])
    z700 = ds_z700[list(ds_z700.data_vars)[0]].squeeze()

    H700 = z700 / 10.0 if float(z700.max()) > 1000 else z700

    ds_rh850 = open_ds(ROOT / cfg["rh850_grib"])
    ds_rh700 = open_ds(ROOT / cfg["rh700_grib"])
    ds_rh500 = open_ds(ROOT / cfg["rh500_grib"])

    try:
        rh850 = ds_rh850[list(ds_rh850.data_vars)[0]].squeeze()
        rh700 = ds_rh700[list(ds_rh700.data_vars)[0]].squeeze()
        rh500 = ds_rh500[list(ds_rh500.data_vars)[0]].squeeze()
    finally:
        ds_rh850.close()
        ds_rh700.close()
        ds_rh500.close()
        
    RH = (rh850 + rh700 + rh500) / 3.0

    # --------------------------------------------------
    # 2) Wrap lon 0–360 -> -180–180
    # --------------------------------------------------
    lats = ds_z700["latitude"].values
    lons = ds_z700["longitude"].values
    lon_wrapped = ((lons + 180.0) % 360.0) - 180.0
    order = np.argsort(lon_wrapped)
    lon_plot = lon_wrapped[order]

    Z = H700.values[:, order]
    RHv = RH.values[:, order]

    # --------------------------------------------------
    # 3) Gridlines + single labels
    # --------------------------------------------------
    gl = ax.gridlines(draw_labels=False, crs=pc, color="black",
                      linewidth=0.4, alpha=0.4, linestyle="dotted", zorder=0)
    gl.xlocator = mticker.FixedLocator(np.arange(-180, 181, cfg["grid_dx"]))
    gl.ylocator = mticker.FixedLocator(np.arange(0, 91, cfg["grid_dy"]))

    ax.text(cfg["lon_label_value"], lat_max - 1.5, f"{abs(cfg['lon_label_value'])}W",
            transform=pc, fontsize=7, alpha=0.65, ha="center", va="center")
    ax.text(lon_min + 1.5, cfg["lat_label_value"], f"{cfg['lat_label_value']}N",
            transform=pc, fontsize=7, alpha=0.65, ha="center", va="center")

    # --------------------------------------------------
    # 4) Base map
    # --------------------------------------------------
    ax.add_feature(cfeature.LAND, facecolor="white", edgecolor="black", linewidth=0.4, zorder=2)
    ax.add_feature(cfeature.COASTLINE, linewidth=0.5, zorder=12)
    ax.add_feature(cfeature.BORDERS, linewidth=0.4, zorder=12)

    provinces = NaturalEarthFeature("cultural", "admin_1_states_provinces_lines", "50m", facecolor="none")
    ax.add_feature(provinces, edgecolor="black", linewidth=0.5, zorder=13)

    if cfg.get("show_fire_boundary", False):
        try:
            fire_gdf = gpd.read_file(ROOT / cfg["fire_outline"])
            fire_feature = ShapelyFeature(fire_gdf.geometry, crs=pc)
            ax.add_feature(
                fire_feature,
                facecolor=cfg.get("fire_facecolor", "none"),
                edgecolor=cfg.get("fire_edgecolor", "0.3"),
                linewidth=cfg.get("fire_linewidth", 1.0),
                zorder=7,
            )
        except Exception as e:
            print("Warning: fire boundary not drawn:", e)

    # --------------------------------------------------
    # 5) Height contours
    # --------------------------------------------------
    hmin, hmax = cfg["height_range"]
    hlev = np.arange(hmin, hmax + cfg["height_interval"], cfg["height_interval"])

    ax.contour(lon_plot, lats, Z,
               levels=hlev, colors="black", linewidths=1.0,
               transform=pc, zorder=5)

    ax.contour(lon_plot, lats, Z,
               levels=cfg["height_highlight"], colors="black", linewidths=2.0,
               transform=pc, zorder=6)

    add_column_labels(
        ax, lon_plot, lats, Z,
        cfg["height_label_lon"], lat_min, lat_max,
        cfg["height_label_levels"], cfg["height_label_tol"], cfg["height_label_min_dlat"],
        pc,
        text_kwargs=dict(fontsize=8,fontweight="bold",color="white"),
        bbox_kwargs=dict(boxstyle="square,pad=0.1", facecolor="black", edgecolor="black", linewidth=0.7),
    )

    # --------------------------------------------------
    # 6) RH shading + contours 
    # --------------------------------------------------
    old_hlw = mpl.rcParams.get("hatch.linewidth", 1.0)
    mpl.rcParams["hatch.linewidth"] = cfg["shade_hatch_lw"]

    if cfg["shade_70_90"]:
        ax.contourf(
            lon_plot, lats, RHv,
            levels=[70, 90],
            colors=[cfg["shade_70_color"]],
            hatches=[cfg["shade_70_90_hatch"]],
            transform=pc,
            zorder=3,
        )

    if cfg["shade_90_plus"]:
        ax.contourf(
            lon_plot, lats, RHv,
            levels=[90, 100],
            colors=[cfg["shade_90_color"]],
            hatches=[cfg["shade_90_plus_hatch"]],
            transform=pc,
            zorder=4,
        )

    mpl.rcParams["hatch.linewidth"] = old_hlw ###### NEW

    ax.contour(
        lon_plot, lats, RHv,
        levels=cfg["rh_levels"],
        colors="black",
        linewidths=cfg["rh_linewidth"],
        linestyles=cfg["rh_linestyle"],
        transform=pc,
        zorder=8,
    )
        
    # --------------------------------------------------
    # 7) Add RH legend for humidity bands
    # --------------------------------------------------       
    
    old_hlw = mpl.rcParams["hatch.linewidth"]
    mpl.rcParams["hatch.linewidth"] = cfg["shade_hatch_lw"]    
    legend_elements = []
    
    # 50–70% RH (contours only)
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
    # 8) H/L centres on 700 hPa height
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

        hi = np.where(is_high)
        lo = np.where(is_low)

        hi_k = thin_pts(hi[0], hi[1], min_dist=cfg["hl_grid_min_dist"])
        lo_k = thin_pts(lo[0], lo[1], min_dist=cfg["hl_grid_min_dist"])

        hi_final = further_thin_latlon(
            hi[0][hi_k], hi[1][hi_k],
            lat_idx, lon_idx, lats, lon_plot, Z,
            min_deg=cfg["hl_deg_min_dist"]
        )
        # lows: sort deepest first by thinning on -Z
        lo_final = further_thin_latlon(
            lo[0][lo_k], lo[1][lo_k],
            lat_idx, lon_idx, lats, lon_plot, -Z,
            min_deg=cfg["hl_deg_min_dist"]
        )

        for iy_s, ix_s in hi_final:
            iy = lat_idx[iy_s]; ix = lon_idx[ix_s]
            draw_HL(ax, float(lon_plot[ix]), float(lats[iy]), "H", float(Z[iy, ix]),
                    pc, lon_min, lon_max, lat_min, lat_max, cfg)

        for iy_s, ix_s in lo_final:
            iy = lat_idx[iy_s]; ix = lon_idx[ix_s]
            draw_HL(ax, float(lon_plot[ix]), float(lats[iy]), "L", float(Z[iy, ix]),
                    pc, lon_min, lon_max, lat_min, lat_max, cfg)

        # --- Hard mask border (drawn in axes coordinates) ---
        import matplotlib.patches as mpatches
        frame = mpatches.Rectangle(
            (0, 0), 1, 1,
            transform=ax.transAxes,
            fill=False,
            edgecolor="black",
            linewidth=1.5,
            zorder=19
        )
        ax.add_patch(frame)
        
    if standalone:
       ax.set_title(cfg["title"], fontsize=10)
    else:
       ax.set_title("")

    if standalone:
      #  fig.tight_layout(pad=cfg.get("tight_layout_pad", 0.2))
        plt.subplots_adjust(**cfg.get("subplots_adjust", {}))
        out_path = OUTDIR / cfg["output_filename"]
        fig.savefig(out_path, dpi=cfg["dpi"])
        print("Saved:", out_path)

    return ax


if __name__ == "__main__":
    plot_700hpa()
