# -*- coding: utf-8 -*-
"""
GDPS MSLP + 1000–500 hPa Thickness (dam)
Supports:
- Standalone mode (creates fig/ax and saves PNG)
- Multi-panel mode (draws onto provided ax)
"""

import os
from pathlib import Path
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib as mpl
import matplotlib.patheffects as PathEffects
import matplotlib.patches as mpatches

import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.feature import NaturalEarthFeature, ShapelyFeature

from scipy.ndimage import maximum_filter, minimum_filter
import geopandas as gpd


# --------------------------------------------------
# FINAL "decided" feature values live here
# --------------------------------------------------
CFG_MSLP = {
    # --- Input files ---
    "mslp_grib": "data/20251119T12Z_MSC_GDPS_Pressure_MSL_LatLon0.15_PT000H.grib2",
    "mslp_index": "mslp.idx",
    "thk_grib": "data/20251119T12Z_MSC_GDPS_Thickness_IsbL-1000to0500_LatLon0.15_PT000H.grib2",
    "thk_index": "thk1000_500.idx",
    "fire_outline": "fire_centers_all.geojson",

    # --- Projection / domain ---
    "central_longitude": -130.0,
    "central_latitude": 50.0,
    "extent": [-170.0, -100.0, 30.0, 75.0],

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

    # ECCC-style boxed MSLP labels along one lon
    "mslp_label_lon": -140.0,
    "mslp_label_tol": 3.0,
    "mslp_label_min_dlat": 0.7,
    "mslp_label_fontsize": 8,

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
    
    # Boxed thickness labels along one lon
    "thk_label_lon": -110.0,
    "thk_label_tol": 3.0,
    "thk_label_min_dlat": 0.7,
    "thk_label_fontsize": 8,

    # --- H/L detection based on MSLP ---
    "show_HL": True,
    "hl_window": 57,
    "hl_grid_min_dist": 8,
    "hl_deg_min_dist": 1.5,

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

    # --- Figure/Output (used only in standalone mode) ---
    "title": "GDPS MSLP + 1000–500 hPa Thickness (dam)",
    "output_dir": "outputs",
    "output_filename": "GDPS_MSLP_thickness.png",
    "dpi": 300,
    "figsize": (10, 7),
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

    pts.sort(reverse=True, key=lambda x: x[0])  # strongest first (for highs)

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


# --------------------------------------------------
# Main plotter
# --------------------------------------------------
def plot_mslp_thickness(cfg=None, ax=None):
    if cfg is None:
        cfg = CFG_MSLP
        
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

    lon_min, lon_max, lat_min, lat_max = cfg["extent"]
    ax.set_extent(cfg["extent"], crs=pc)

    # --- Open data ---
    ds_msl = open_ds(ROOT / cfg["mslp_grib"])
    ds_thk = open_ds(ROOT / cfg["thk_grib"])

    try:
       msl = ds_msl[list(ds_msl.data_vars)[0]].squeeze()
       thk = ds_thk[list(ds_thk.data_vars)[0]].squeeze()
    finally:
       ds_msl.close()
       ds_thk.close()
       
    mslp = msl / 100.0  # Pa -> hPa

    thk_vals = thk.values
    thickness = thk / 10.0 if float(np.nanmax(thk_vals)) > 1000 else thk  # gpm -> dam if needed

    lats = ds_msl["latitude"].values
    lons = ds_msl["longitude"].values

    lon_wrapped = ((lons + 180.0) % 360.0) - 180.0
    order = np.argsort(lon_wrapped)
    lon_plot = lon_wrapped[order]

    Z = mslp.values[:, order]
    T = thickness.values[:, order]

    # --- Gridlines + single labels ---
    gl = ax.gridlines(draw_labels=False, crs=pc, color="black", linewidth=0.4,
                      alpha=0.4, linestyle="dotted", zorder=0)
    gl.xlocator = mticker.FixedLocator(np.arange(-180, 181, cfg["grid_dx"]))
    gl.ylocator = mticker.FixedLocator(np.arange(0, 91, cfg["grid_dy"]))

    ax.text(cfg["lon_label_value"], lat_max - 1.5, f"{abs(cfg['lon_label_value'])}W",
            transform=pc, fontsize=cfg["label_fontsize"], alpha=cfg["label_alpha"],
            ha="center", va="center")
    ax.text(lon_min + 1.5, cfg["lat_label_value"], f"{cfg['lat_label_value']}N",
            transform=pc, fontsize=cfg["label_fontsize"], alpha=cfg["label_alpha"],
            ha="center", va="center")

    # --- Base map features ---
    ax.add_feature(cfeature.LAND, edgecolor="black", facecolor="white", linewidth=0.4, zorder=2)
    ax.add_feature(cfeature.COASTLINE, linewidth=cfg["coastline_lw"], zorder=12)
    ax.add_feature(cfeature.BORDERS, linewidth=cfg["borders_lw"], zorder=12)

    provinces = NaturalEarthFeature("cultural", "admin_1_states_provinces_lines", "50m", facecolor="none")
    ax.add_feature(provinces, edgecolor="black", linewidth=cfg["province_lw"], zorder=13)

    if cfg["show_fire_boundary"]:
        try:
            fire_gdf = gpd.read_file(ROOT / cfg["fire_outline"])
            fire_feature = ShapelyFeature(fire_gdf.geometry, crs=pc)
            ax.add_feature(
                fire_feature,
                edgecolor=cfg["fire_edgecolor"],
                facecolor=cfg["fire_facecolor"],
                linewidth=cfg["fire_linewidth"],
                zorder=2,
            )
        except Exception as e:
            print("Warning: fire boundary not drawn:", e)

    # --- MSLP contours ---
    msl_levels = np.array(cfg["mslp_levels"])
    ax.contour(lon_plot, lats, Z, levels=msl_levels,
               colors="black", linewidths=cfg["mslp_linewidth"],
               transform=pc, zorder=5)

    hlv = np.array(cfg["mslp_highlight_levels"])
    if hlv.size > 0:
        ax.contour(lon_plot, lats, Z, levels=hlv,
                   colors="black", linewidths=cfg["mslp_highlight_linewidth"],
                   transform=pc, zorder=6)

    # Boxed MSLP labels along one longitude
    label_lon = cfg["mslp_label_lon"]
    idx_lon = int(np.argmin(np.abs(lon_plot - label_lon)))
    lat_mask = (lats >= lat_min) & (lats <= lat_max)
    lats_sub = lats[lat_mask]
    Z_col = Z[:, idx_lon][lat_mask]

    used_lats = []
    for lev in msl_levels:
        if Z_col.size == 0:
            continue
        iy = int(np.argmin(np.abs(Z_col - lev)))
        if float(np.abs(Z_col[iy] - lev)) > cfg["mslp_label_tol"]:
            continue
        lat_lab = float(lats_sub[iy])
        if any(abs(lat_lab - u) < cfg["mslp_label_min_dlat"] for u in used_lats):
            continue
        used_lats.append(lat_lab)
        # This version will make the boxed labels go partly outside the map
        # ax.text(
        #     label_lon, lat_lab, f"{int(lev)}",
        #     transform=pc, ha="center", va="center",
        #     fontsize=cfg["mslp_label_fontsize"], color="white",
        #     bbox=dict(boxstyle="square,pad=0.1", facecolor="black",
        #               edgecolor="black", linewidth=0.7),
        #     zorder=20
        # )
        # Maintains boxed labels inside the plot
        txt = ax.text(
            label_lon, lat_lab, f"{int(lev)}",
            transform=pc, ha="center", va="center",
            fontsize=cfg["mslp_label_fontsize"], color="white",
            bbox=dict(boxstyle="square,pad=0.1", facecolor="black",
                      edgecolor="black", linewidth=0.7),
            zorder=20
            )
        txt.set_clip_on(True)
        txt.set_clip_path(ax.patch)

    # --- Thickness shaded band (hatched) + contours ---
    old_hlw = mpl.rcParams.get("hatch.linewidth", 1.0)
    if cfg["shade_band"]:
        mpl.rcParams["hatch.linewidth"] = cfg["shade_hatch_linewidth"]
        ax.contourf(
            lon_plot, lats, T,
            levels=[cfg["shade_min"], cfg["shade_max"]],
            colors="none",
            hatches=[cfg["shade_hatch"]],
            transform=pc,
            zorder=4
        )
    mpl.rcParams["hatch.linewidth"] = old_hlw

    thk_levels = np.array(cfg["thk_levels"])
    ax.contour(lon_plot, lats, T, levels=thk_levels,
               colors="black", linewidths=cfg["thk_linewidth"],
               linestyles=cfg["thk_linestyle"],
               transform=pc, zorder=7)

    # Boxed thickness labels along one longitude
    t_lon = cfg["thk_label_lon"]
    t_idx_lon = int(np.argmin(np.abs(lon_plot - t_lon)))
    T_col = T[:, t_idx_lon][lat_mask]
    lats_sub_thk = lats[lat_mask]

    used_thk = []
    for lev in thk_levels:
        if T_col.size == 0:
            continue
        iy = int(np.argmin(np.abs(T_col - lev)))
        if float(np.abs(T_col[iy] - lev)) > cfg["thk_label_tol"]:
            continue
        lat_lab = float(lats_sub_thk[iy])
        if any(abs(lat_lab - u) < cfg["thk_label_min_dlat"] for u in used_thk):
            continue
        used_thk.append(lat_lab)

        ax.text(
            t_lon, lat_lab, f"{int(lev)}",
            transform=pc, ha="center", va="center",
            fontsize=cfg["thk_label_fontsize"], color="black",
            bbox=dict(boxstyle="square,pad=0.1", facecolor="none",
                      edgecolor="black", linewidth=0.5),
            zorder=20
        )

        # --- Hard mask border (drawn in axes coordinates) ---
       # import matplotlib.patches as mpatches
        frame = mpatches.Rectangle(
            (0, 0), 1, 1,
            transform=ax.transAxes,
            fill=False,
            edgecolor="black",
            linewidth=1.5,
            zorder=19
        )
        ax.add_patch(frame)
        
    # --- H/L centres from MSLP field ---
    if cfg["show_HL"]:
        lat_mask_full = (lats >= lat_min) & (lats <= lat_max)
        lon_mask_full = (lon_plot >= lon_min) & (lon_plot <= lon_max)
        lat_idx = np.where(lat_mask_full)[0]
        lon_idx = np.where(lon_mask_full)[0]

        Z_sub = Z[np.ix_(lat_idx, lon_idx)]

        win = cfg["hl_window"]
        zmax = maximum_filter(Z_sub, size=win)
        zmin = minimum_filter(Z_sub, size=win)

        is_high = (Z_sub == zmax)
        is_low = (Z_sub == zmin)

        hi = np.where(is_high)
        lo = np.where(is_low)

        hi_k = thin_pts(hi[0], hi[1], min_dist=cfg["hl_grid_min_dist"])
        lo_k = thin_pts(lo[0], lo[1], min_dist=cfg["hl_grid_min_dist"])

        hi_final = further_thin_latlon(hi[0][hi_k], hi[1][hi_k], lat_idx, lon_idx,
                                       lats, lon_plot, Z, min_deg=cfg["hl_deg_min_dist"])
        # lows: we want deepest first, so pass negative field to reuse same sorter
        lo_final = further_thin_latlon(lo[0][lo_k], lo[1][lo_k], lat_idx, lon_idx,
                                       lats, lon_plot, -Z, min_deg=cfg["hl_deg_min_dist"])

        for iy_s, ix_s in hi_final:
            iy = lat_idx[iy_s]; ix = lon_idx[ix_s]
            draw_HL(ax, float(lon_plot[ix]), float(lats[iy]), "H", float(Z[iy, ix]),
                    pc, lon_min, lon_max, lat_min, lat_max, cfg)

        for iy_s, ix_s in lo_final:
            iy = lat_idx[iy_s]; ix = lon_idx[ix_s]
            draw_HL(ax, float(lon_plot[ix]), float(lats[iy]), "L", float(Z[iy, ix]),
                    pc, lon_min, lon_max, lat_min, lat_max, cfg)

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
            
                
    if standalone:
       ax.set_title(cfg["title"], fontsize=10)
    else:
       ax.set_title("")


    if standalone:
       # fig.tight_layout(pad=cfg["tight_layout_pad"])
        plt.subplots_adjust(**cfg["subplots_adjust"])
        out_path = OUTDIR / cfg["output_filename"]
        fig.savefig(out_path, dpi=cfg["dpi"])
        print("Saved:", out_path)

    return ax


if __name__ == "__main__":
    plot_mslp_thickness()
