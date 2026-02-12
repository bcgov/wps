# -*- coding: utf-8 -*-
"""
GDPS 500 hPa Geopotential Height (dam) + Relative Vorticity
Styled to match the MSLP + thickness chart:
- Same projection, extent, BCWS boundary, gridlines
- Highlight 528, 546, 570 dam with thicker lines
- Relative vorticity as thin contours
- ECCC-style H/L symbols based on 500-hPa height
"""

import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.feature import NaturalEarthFeature
from scipy.ndimage import maximum_filter, minimum_filter
import matplotlib.ticker as mticker
from pathlib import Path
import matplotlib.patheffects as PathEffects
import geopandas as gpd
from cartopy.feature import ShapelyFeature
import os

# --------------------------------------------------
# Helper to open GRIB with cfgrib + index file
# --------------------------------------------------
def open_ds(grib_path: Path, indexname: str) -> xr.Dataset:
    return xr.open_dataset(
        grib_path,
        engine="cfgrib",
        backend_kwargs={"indexpath": indexname},
    )

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
# --------------------------------------------------
# 1. EDIT THESE PATHS
# --------------------------------------------------
# 500-hPa geopotential height
f_z500 = ROOT / "data/20251121T12Z_MSC_GDPS_GeopotentialHeight_IsbL-0500_LatLon0.15_PT000H.grib2"

# 500-hPa RELATIVE vorticity (the EC file you mentioned)
f_vort = ROOT / "data/20251121T12Z_MSC_GDPS_RelativeVorticity_IsbL-0500_LatLon0.15_PT000H.grib2"


# f_vort = Path(
#     r"20251121T12Z_MSC_GDPS_AbsoluteVorticity_IsbL-0500_LatLon0.15_PT000H.grib2"
# )

# Same fire-centre outline you used in the MSL script
fire_outline_path = ROOT / "fire_centers_all.geojson"


# --------------------------------------------------
# 2. Open datasets and prepare fields
# --------------------------------------------------
ds_z500 = open_ds(f_z500, "z500.idx")
ds_vort = open_ds(f_vort, "rv500.idx")

z_var = list(ds_z500.data_vars)[0]       # e.g. 'gh'
v_var = list(ds_vort.data_vars)[0]       # e.g. 'absvor' or 'vo'

z_raw = ds_z500[z_var].squeeze(drop=True)
v_raw = ds_vort[v_var].squeeze(drop=True)

# Geopotential height:
# convert to dam
z_vals = z_raw.values
if z_vals.max() > 1000:          # assume metres
    H500 = z_raw / 10.0          # -> decametres (dam)
else:
    H500 = z_raw                 # already dam

# Relative vorticity: convert to 1e-5 s^-1 for plotting
# (matching "+ - ...8,10,12... (1.E-5)/s" style)
V_raw = v_raw.values
# make sure we don't blow up if units are already scaled
if np.nanmax(np.abs(V_raw)) < 1e-3:
    vort = v_raw * 1e5   
    print("unit convert works")        # from s^-1 to 1e-5 s^-1
else:
    vort = v_raw * 1e5                 # 

# Coordinates (model grid)
lats_1d = ds_z500["latitude"].values    # (ny,)
lons_1d = ds_z500["longitude"].values   # (nx,) in 0–360

# Wrap longitude 0–360 -> -180–180 AND reorder fields consistently
lon_wrapped = ((lons_1d + 180.0) % 360.0) - 180.0
order = np.argsort(lon_wrapped)
lon_plot = lon_wrapped[order]

Z_full = H500.values
V_full = vort.values

Z = Z_full[:, order]
V = V_full[:, order]

ny, nx = Z.shape

# BCWS boundaries
fire_gdf = gpd.read_file(fire_outline_path)

# --------------------------------------------------
# 3. Plot setup (same as MSL)
# --------------------------------------------------
proj = ccrs.LambertConformal(central_longitude=-130, central_latitude=50)
pc   = ccrs.PlateCarree()

plt.rcParams["font.size"] = 7
plt.rcParams["axes.linewidth"] = 0.3

fig = plt.figure(figsize=(10, 7))
ax = plt.axes(projection=proj)

# Same domain as your current MSL map
lon_min, lon_max = -170, -100
lat_min, lat_max = 30, 75
extent = [lon_min, lon_max, lat_min, lat_max]
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
gl.xlocator = mticker.FixedLocator(np.arange(-180, 181, 5))
gl.ylocator = mticker.FixedLocator(np.arange(0, 91, 5))

lon_label_value = -140          # 140W
lon_label_y_pos = lat_max - 1.5

lat_label_value = 40            # 40N
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
ax.add_feature(cfeature.LAND, edgecolor="black", facecolor="white", linewidth=0.4)
ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
ax.add_feature(cfeature.BORDERS, linewidth=0.4)

provinces = NaturalEarthFeature(
    "cultural",
    "admin_1_states_provinces_lines",
    "50m",
    facecolor="none"
)
ax.add_feature(provinces, edgecolor="black", linewidth=0.5)

# Fire center boundary can be turned on/off
# fire_feature = ShapelyFeature(
#     fire_gdf.geometry,
#     crs=pc,
# )
# ax.add_feature(
#     fire_feature,
#     edgecolor="0.3",
#     facecolor="none",
#     linewidth=1,
#     zorder=1
# )

# --------------------------------------------------
# 4. 500-hPa HEIGHT contours (dam)
# --------------------------------------------------
# Heights every 6 dam
h_levels = np.arange(480, 600, 6)
highlight_h = [528, 546, 570]

# Base 500-hPa height contours (thin)
cs_h = ax.contour(
    lon_plot, lats_1d, Z,
    levels=h_levels,
    colors="black",
    linewidths=1.0,
    transform=pc,
    zorder=5
)

# Highlight 528 / 546 / 570 with thicker lines
ax.contour(
    lon_plot, lats_1d, Z,
    levels=highlight_h,
    colors="black",
    linewidths=2.0,
    transform=pc,
    zorder=6
)

# EC-style: boxed height labels along a fixed longitude (e.g., -140°)
label_lon_h = -140.0
idx_lon_h = np.argmin(np.abs(lon_plot - label_lon_h))

lat_mask_h = (lats_1d >= lat_min) & (lats_1d <= lat_max)
lats_sub_h = lats_1d[lat_mask_h]
Z_col_full = Z[:, idx_lon_h]
Z_col = Z_col_full[lat_mask_h]

tol_dam = 3.0             # how close column value must be to label level
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
# 5. Relative vorticity contours (1e-5 s^-1)
# --------------------------------------------------
# Symmetric levels; adjust once you see how noisy it looks
v_levels = np.arange(-16, 16, 8)  # -12,-10,...,10,12
#v_levels = np.arange(-25, 26, 2)

cs_v = ax.contour(
    lon_plot, lats_1d, V,
    levels=v_levels,
    colors="black",
    linewidths=0.5,
    linestyles="dashed",  # very light "sigma" feel; tweak if you like
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

# local extrema on trimmed grid
win = 51
zmax = maximum_filter(Z_sub, size=win)
zmin = minimum_filter(Z_sub, size=win)

is_high = (Z_sub == zmax)
is_low  = (Z_sub == zmin)

sub_hi = np.where(is_high)
sub_lo = np.where(is_low)

def thin_pts(iy, ix, min_dist=8):
    kept = []
    for j in range(len(iy)):
        y, x = iy[j], ix[j]
        if all((y - iy[k])**2 + (x - ix[k])**2 >= min_dist**2 for k in kept):
            kept.append(j)
    return kept

hi_k = thin_pts(sub_hi[0], sub_hi[1], min_dist=8)
lo_k = thin_pts(sub_lo[0], sub_lo[1], min_dist=8)

def further_thin_latlon(iy_sub, ix_sub, lat_idx, lon_idx,
                        lats_1d, lon_plot, Z, min_deg=1.5):
    pts = []
    for iy_s, ix_s in zip(iy_sub, ix_sub):
        iy_global = lat_idx[iy_s]
        ix_global = lon_idx[ix_s]
        lat = float(lats_1d[iy_global])
        lon = float(lon_plot[ix_global])
        val = float(Z[iy_global, ix_global])
        pts.append((val, iy_s, ix_s, lat, lon))

    # strongest/highest first for 500 hPa
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

hi_final = further_thin_latlon(
    sub_hi[0][hi_k], sub_hi[1][hi_k],
    lat_idx, lon_idx, lats_1d, lon_plot, Z,
    min_deg=1.5
)
lo_final = further_thin_latlon(
    sub_lo[0][lo_k], sub_lo[1][lo_k],
    lat_idx, lon_idx, lats_1d, lon_plot, Z,
    min_deg=1.5
)

def draw_HL(ax, lon, lat, letter, val, pc,
            lon_min, lon_max, lat_min, lat_max):
    """
    EC-style 500-hPa H/L symbol, with halo.
    Suppresses labels that would fall outside the map.
    """
    d_letter = 1.5   # deg above centre
    d_value  = 1.2   # deg below centre

    lat_letter = lat + d_letter
    lat_center = lat
    lat_value  = lat - d_value

    pad_lon = 1.0
    pad_lat = 1.0

    if (
        (lon < lon_min + pad_lon) or (lon > lon_max - pad_lon) or
        (lat_letter > lat_max - pad_lat) or
        (lat_value  < lat_min + pad_lat)
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

# Plot highs (ridges)
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

# Plot lows (trough centres)
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


# Positive and negative symbols

# --------------------------------------------------
# 6b. Vorticity '+' and '−' centres (sigma-style markers)
# --------------------------------------------------
# Use same trimmed domain (lat_idx, lon_idx) as H/L
V_sub = V[np.ix_(lat_idx, lon_idx)]

# local extrema for vorticity (smaller window to keep features)
win_v = 39
vmax = maximum_filter(V_sub, size=win_v)
vmin = minimum_filter(V_sub, size=win_v)

is_pos = (V_sub == vmax)
is_neg = (V_sub == vmin)

# Magnitude threshold in 1e-5 s^-1 (ECCC uses ...8,10,12...)
vort_thresh = 0
is_pos &= (V_sub > vort_thresh)
is_neg &= (V_sub < -vort_thresh)

pos_idx = np.where(is_pos)
neg_idx = np.where(is_neg)

# thin in grid space first
pos_k = thin_pts(pos_idx[0], pos_idx[1], min_dist=6)
neg_k = thin_pts(neg_idx[0], neg_idx[1], min_dist=6)

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
        pts.sort(key=lambda x: x[0])   # most negative first

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

pos_final = further_thin_vort(
    pos_idx[0][pos_k], pos_idx[1][pos_k],
    lat_idx, lon_idx, lats_1d, lon_plot, V_sub,
    min_deg=1.0, positive=True
)
neg_final = further_thin_vort(
    neg_idx[0][neg_k], neg_idx[1][neg_k],
    lat_idx, lon_idx, lats_1d, lon_plot, V_sub,
    min_deg=1.0, positive=False
)

def draw_vort_symbol(ax, lon, lat, sign, value, pc,
                     lon_min, lon_max, lat_min, lat_max):
    """
    Draw '+ / −' with the ECCC-style halo + numerical value below.
    """
    pad = 0.5
    if not (lon_min + pad <= lon <= lon_max - pad and
            lat_min + pad <= lat <= lat_max - pad):
        return
    
    # ------- SYMBOL (+ or -) -------
    txt = ax.text(
        lon, lat + 0.4, sign,
        transform=pc,
        ha="center", va="center",
        fontsize=5, #fontweight="bold",
        color="black", zorder=10,
    )
    txt.set_path_effects([
        PathEffects.Stroke(linewidth=1.8, foreground="white"),
        PathEffects.Normal()
    ])

    # ------- VALUE (integer) -------
    val_txt = ax.text(
        lon, lat - 0.3, f"{int(abs(value))}",
        transform=pc,
        ha="center", va="center",
        fontsize=5, #fontweight="bold",
        color="black", zorder=10,
    )
    val_txt.set_path_effects([
        PathEffects.Stroke(linewidth=1.5, foreground="white"),
        PathEffects.Normal()
    ])


# ------------ DRAW POSITIVE VORTICITY ------------
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

# ------------ DRAW NEGATIVE VORTICITY ------------
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
ax.set_title("GDPS 500 hPa Height (dam) + Relative Vorticity (1e-5 s⁻¹)", fontsize=10)

plt.savefig(OUTPUT_DIR / "GDPS_500hPa_Height_Vorticity_ECCCstyle.png", dpi=300)
plt.show()
