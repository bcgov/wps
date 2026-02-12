# -*- coding: utf-8 -*-
"""
GDPS MSLP + 1000–500 hPa Thickness (dam) with ECCC-style H/L symbols
and ECCC-style boxed MSLP labels.
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
import matplotlib as mpl
import matplotlib.transforms as mtransforms
from matplotlib.patches import FancyBboxPatch
import geopandas as gpd
from cartopy.feature import ShapelyFeature
import matplotlib.patheffects as PathEffects
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


def label_thickness_EC(ax, cs, levels, angle_offset=-110, fontsize=7):
    """
    Place boxed thickness labels (facecolor=none) for given levels.
    Boxes are rotated to follow contour orientation, offset by angle_offset degrees.
    """
    pc = ccrs.PlateCarree()

    for lev in levels:
        # Find the contour collection matching this level
        try:
            idx = list(cs.levels).index(lev)
        except ValueError:
            print(f"Thickness level {lev} not found in contour set.")
            continue

        coll = cs.collections[idx]

        # Extract all line segments for this level
        paths = coll.get_paths()
        if not paths:
            continue

        # pick the longest path (usually the main closed contour)
        main_path = max(paths, key=lambda p: len(p.vertices))

        verts = main_path.vertices
        xs = verts[:, 0]
        ys = verts[:, 1]

        # pick the midpoint of the contour for label placement
        mid = len(xs) // 2
        x0, y0 = xs[mid], ys[mid]

        # Compute local tangent angle
        if mid < len(xs) - 1:
            dx = xs[mid+1] - xs[mid-1]
            dy = ys[mid+1] - ys[mid-1]
        else:
            dx = xs[mid] - xs[mid-2]
            dy = ys[mid] - ys[mid-2]

        angle = np.degrees(np.arctan2(dy, dx))

        # Apply EC offset (−120° as requested)
        final_angle = angle + angle_offset

        # Create the rotated, boxed label
        trans = mtransforms.Affine2D().rotate_deg_around(x0, y0, final_angle) + ax.transData

        ax.text(
            x0, y0, f"{lev}",
            transform=trans,
            fontsize=fontsize,
            ha="center", va="center",
            bbox=dict(
                boxstyle="square,pad=0.15",
                facecolor="none",
                edgecolor="black",
                linewidth=0.8
            ),
            zorder=15
        )



# --------------------------------------------------
# 1. EDIT THESE PATHS
# --------------------------------------------------
f_msl = ROOT / "data/20251119T12Z_MSC_GDPS_Pressure_MSL_LatLon0.15_PT000H.grib2"

f_thk = ROOT / "data/20251119T12Z_MSC_GDPS_Thickness_IsbL-1000to0500_LatLon0.15_PT000H.grib2"


fire_outline_path = ROOT / "fire_centers_all.geojson"

# --------------------------------------------------
# 2. Open datasets and prepare fields
# --------------------------------------------------
ds_msl = open_ds(f_msl, "mslp.idx")
ds_thk = open_ds(f_thk, "thk1000_500.idx")

msl_var = list(ds_msl.data_vars)[0]
thk_var = list(ds_thk.data_vars)[0]

msl_raw = ds_msl[msl_var].squeeze(drop=True)   # Pa
thk_raw = ds_thk[thk_var].squeeze(drop=True)   # gpm or dam

# MSLP: Pa -> hPa
mslp = msl_raw / 100.0

# Thickness: detect units
thk_vals = thk_raw.values
if thk_vals.max() > 1000:          # assume gpm
    thickness = thk_raw / 10.0     # -> dam
else:
    thickness = thk_raw            # already dam

# Coordinates (model grid)
lats_1d = ds_msl["latitude"].values    # (ny,) typically 90→-90
lons_1d = ds_msl["longitude"].values   # (nx,) in 0–360

# Wrap longitude 0–360 -> -180–180 AND reorder fields consistently
lon_wrapped = ((lons_1d + 180.0) % 360.0) - 180.0
order = np.argsort(lon_wrapped)
lon_plot = lon_wrapped[order]

Z_full = mslp.values                     # (ny, nx)
T_full = thickness.values

Z = Z_full[:, order]                     # reorder to match lon_plot
T = T_full[:, order]

ny, nx = Z.shape

# BCWS boundaries
# --------------------------------------------------
# Fire Centre boundary (bold outline, no fill)
# --------------------------------------------------
fire_gdf = gpd.read_file(fire_outline_path)


# --------------------------------------------------
# 3. Plot setup
# --------------------------------------------------
proj = ccrs.LambertConformal(central_longitude=-130, central_latitude=50)
pc   = ccrs.PlateCarree()

plt.rcParams["font.size"] = 7
plt.rcParams["axes.linewidth"] = 0.3

fig = plt.figure(figsize=(10, 7))
ax = plt.axes(projection=proj)

# ----- DESIRED EXTENT -----
lon_min, lon_max = -170, -100
lat_min, lat_max = 35, 75
extent = [lon_min, lon_max, lat_min, lat_max]
ax.set_extent(extent, crs=pc)

# --------------------------------------------------
# Lat/Lon grid
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
lon_label_y_pos = lat_max - 1.5 # slightly above bottom boundary

lat_label_value = 40            # 40N
lat_label_x_pos = lon_min + 1.5 # slightly inside left boundary

label_style = dict(
    fontsize=7,
    color="black",
    alpha=0.65,
    ha="center",
    va="center"
)

# Draw ONLY ONE longitude label (inside map)
ax.text(
    lon_label_value,
    lon_label_y_pos,
    f"{abs(lon_label_value)}W",
    transform=pc,
    **label_style
)

# Draw ONLY ONE latitude label (inside map)
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
ax.add_feature(provinces, edgecolor='black', linewidth=0.5)

fire_feature = ShapelyFeature(
    fire_gdf.geometry,
    crs=pc,              # geojson is in lat/lon (PlateCarree)
)

ax.add_feature(
    fire_feature,
    edgecolor="0.3",
    facecolor="none",
    linewidth=0.4,       # slightly thicker than provinces
    zorder=1           # above provinces, below H/L and labels
)

# ax.add_geometries(
#     fire_gdf.geometry,
#     crs=pc,
#     facecolor="none",
#     edgecolor="black",
#     linewidth=1.2,
#     hatch="xx",          # or "//", choose something distinct from 534–540 shading
#     zorder=1.5
# )

# --------------------------------------------------
# 4. MSLP contours – ECCC-style boxed labels (column method)
# --------------------------------------------------

msl_levels = np.arange(960, 1050, 4)

# Base contours (thin)
cs_msl = ax.contour(
    lon_plot, lats_1d, Z,
    levels=msl_levels,
    colors="black",
    linewidths=1,
    transform=pc
)

# Optionally make selected MSLP levels thicker (e.g., 1000 / 1024)
highlight_msl = [1000, 1024]
ax.contour(
    lon_plot, lats_1d, Z,
    levels=highlight_msl,
    colors="black",
    linewidths=2,
    transform=pc
)

# --- ECCC-style: boxed labels for ALL MSLP levels along one longitude ---

label_lon = -140.0  # longitude where labels align vertically
idx_lon = np.argmin(np.abs(lon_plot - label_lon))

# restrict to latitudes inside the map
lat_mask = (lats_1d >= lat_min) & (lats_1d <= lat_max)
lats_sub = lats_1d[lat_mask]
Z_col_full = Z[:, idx_lon]
Z_col = Z_col_full[lat_mask]

# simple tolerance: only label if the column actually gets near that level
tol_hpa = 3.0

# to avoid labels too close to each other
used_lats = []

for lev in msl_levels:
    if Z_col.size == 0:
        continue

    # find closest point in column
    iy_rel = int(np.argmin(np.abs(Z_col - lev)))
    diff = float(np.abs(Z_col[iy_rel] - lev))

    if diff > tol_hpa:
        # contour of this level may not really cross this longitude
        continue

    lat_lab = float(lats_sub[iy_rel])

    # enforce minimum separation in latitude (deg)
    if any(abs(lat_lab - ulat) < 0.7 for ulat in used_lats):
        continue
    used_lats.append(lat_lab)

    ax.text(
        label_lon, lat_lab, f"{int(lev)}",
        transform=pc,
        ha="center", va="center",
        fontsize=6,
        color="white",
        bbox=dict(
            boxstyle="square,pad=0.1",
            facecolor="black",
            edgecolor="black",
            linewidth=0.7
        ),
        zorder=8
    )

# --------------------------------------------------
# 5. Thickness contours + shaded 534–540 band
# --------------------------------------------------
all_thk = np.arange(480, 600, 6)

# --- temporarily make hatch lines very thin => smaller dots ---
old_hlw = mpl.rcParams.get("hatch.linewidth", 1.0)
mpl.rcParams["hatch.linewidth"] = 0.15   # try 0.1–0.2 for tiny dots

# shaded band 534–540 dam with dot hatch
band_min, band_max = 534, 540
cs_band = ax.contourf(
    lon_plot, lats_1d, T,
    levels=[band_min, band_max],
    colors="none",
    hatches=["....."],     # more dots; try '..' or '...' to adjust density
    transform=pc,
    zorder=6
)

# style hatch outlines (Cartopy-safe)
for coll in cs_band.legend_elements()[0]:
    try:
        coll.set_edgecolor("black")
        coll.set_linewidth(0.3)   # border around shaded area
    except Exception:
        pass

# restore default hatch linewidth for everything else
mpl.rcParams["hatch.linewidth"] = old_hlw

# dashed thickness lines on top
cs_thk = ax.contour(
    lon_plot, lats_1d, T,
    levels=all_thk,
    colors="black",
    linewidths=1.0,
    linestyles="dashed",
    transform=pc,
    zorder=7
)
#ax.clabel(cs_thk, fmt="%d", fontsize=6)

# --- ECCC-style boxed thickness labels along lon = -120 ---
thk_label_levels = all_thk        # or e.g. [528, 534, 540, 546, 552]
label_lon_thk = -110.0            # longitude for the vertical column of labels

idx_lon_thk = np.argmin(np.abs(lon_plot - label_lon_thk))

# limit to latitudes inside map extent
lat_mask_thk = (lats_1d >= lat_min) & (lats_1d <= lat_max)
lats_sub_thk = lats_1d[lat_mask_thk]
T_col_full = T[:, idx_lon_thk]
T_col = T_col_full[lat_mask_thk]

tol_dam = 3.0       # only label if column actually gets near that thickness level
used_lats_thk = []  # avoid labels too close vertically

for lev in thk_label_levels:
    if T_col.size == 0:
        continue

    iy_rel = int(np.argmin(np.abs(T_col - lev)))
    diff = float(np.abs(T_col[iy_rel] - lev))

    if diff > tol_dam:
        # thickness contour for this level likely doesn't cross this longitude
        continue

    lat_lab = float(lats_sub_thk[iy_rel])

    # enforce minimum separation between labels in latitude (deg)
    if any(abs(lat_lab - ulat) < 0.7 for ulat in used_lats_thk):
        continue
    used_lats_thk.append(lat_lab)

    ax.text(
        label_lon_thk, lat_lab, f"{int(lev)}",
        transform=pc,
        ha="center", va="center",
        fontsize=6,
        color="black",
        bbox=dict(
            boxstyle="square,pad=0.1",
            facecolor="none",     # HOLLOW box for thickness
            edgecolor="black",
            linewidth=0.5
        ),
        zorder=8
    )


# --------------------------------------------------
# 6. High / Low centres *ONLY INSIDE THE EXTENT*
# --------------------------------------------------

# mask of lat/lon within extent
lat_mask_full = (lats_1d >= lat_min) & (lats_1d <= lat_max)
lon_mask_full = (lon_plot >= lon_min) & (lon_plot <= lon_max)

lat_idx = np.where(lat_mask_full)[0]
lon_idx = np.where(lon_mask_full)[0]

Z_sub = Z[np.ix_(lat_idx, lon_idx)]

# local extrema on trimmed grid
win =57
zmax = maximum_filter(Z_sub, size=win)
zmin = minimum_filter(Z_sub, size=win)

is_high = (Z_sub == zmax)
is_low  = (Z_sub == zmin)

# convert subgrid indices back to global
sub_hi = np.where(is_high)
sub_lo = np.where(is_low)

# thinning in grid space
def thin_pts(iy, ix, min_dist=8):
    kept = []
    for j in range(len(iy)):
        y, x = iy[j], ix[j]
        if all((y - iy[k])**2 + (x - ix[k])**2 >= min_dist**2 for k in kept):
            kept.append(j)
    return kept

hi_k = thin_pts(sub_hi[0], sub_hi[1], min_dist=8)
lo_k = thin_pts(sub_lo[0], sub_lo[1], min_dist=8)

# --------------------------------------------------
# 6b. EXTRA LAT/LON THINNING (remove duplicate centres)
# --------------------------------------------------
def further_thin_latlon(iy_sub, ix_sub, lat_idx, lon_idx,
                        lats_1d, lon_plot, Z, min_deg=1.5):
    """
    Remove centres closer than min_deg (~150 km).
    Always keeps the strongest system first.
    iy_sub, ix_sub are indices inside Z_sub (not global!)
    """
    pts = []
    for iy_s, ix_s in zip(iy_sub, ix_sub):
        iy_global = lat_idx[iy_s]
        ix_global = lon_idx[ix_s]
        lat = float(lats_1d[iy_global])
        lon = float(lon_plot[ix_global])
        val = float(Z[iy_global, ix_global])
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

# Apply to highs and lows
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

# --------------------------------------------------
# Draw H/L symbols
# --------------------------------------------------
def draw_HL(ax, lon, lat, letter, val, pc,
            lon_min, lon_max, lat_min, lat_max):
    """
    ECCC-style high/low symbol, but ONLY if the whole
    label stack fits inside the map extent.
    """

    # how far above/below the centre we draw things
    d_letter = 1.5   # deg above centre
    d_value  = 1.2   # deg below centre

    # positions we are going to use
    lat_letter = lat + d_letter
    lat_center = lat
    lat_value  = lat - d_value

    # require a little margin from all edges
    pad_lon = 1.0
    pad_lat = 1.0

    if (
        (lon < lon_min + pad_lon) or (lon > lon_max - pad_lon) or
        (lat_letter > lat_max - pad_lat) or
        (lat_value  < lat_min + pad_lat)
    ):
        # Not enough room – do not draw this H/L at all
        return

    # 1. Letter (H or L) with white halo
    txt = ax.text(
        lon, lat_letter, letter,
        transform=pc,
        ha="center", va="center",
        fontsize=20, fontweight="bold",
        color="black", zorder=12,
    )
    txt.set_path_effects([
        PathEffects.Stroke(linewidth=3, foreground="white"),
        PathEffects.Normal()
    ])

    # 2. Circle with X
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

    # 3. Pressure number
    num = ax.text(
        lon, lat_value, f"{int(val)}",
        transform=pc,
        ha="center", va="center",
        fontsize=8, fontweight="bold",
        color="black", zorder=12,
    )
    num.set_path_effects([
        PathEffects.Stroke(linewidth=2, foreground="white"),
        PathEffects.Normal()
    ])
    
# highs
for iy_s, ix_s in hi_final:
    iy = lat_idx[iy_s]
    ix = lon_idx[ix_s]
    draw_HL(ax, float(lon_plot[ix]),float(lats_1d[iy]), "H", float(Z[iy, ix]), pc, lon_min, lon_max, lat_min, lat_max)


# lows
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
    lon_min, lon_max, lat_min, lat_max   # <-- add these
)

# --------------------------------------------------
# 7. Title
# --------------------------------------------------
ax.set_title("GDPS MSLP + 1000–500 hPa Thickness (dam)", fontsize=10)

plt.savefig(OUTPUT_DIR / "GDPS_small_domain_ECCCstyle.png", dpi=300)
plt.show()
