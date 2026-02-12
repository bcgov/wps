from pathlib import Path
import re
import streamlit as st
from PIL import Image

st.set_page_config(layout="wide")

# ---- point this to where you save your 4-panel images ----
# Example folder: outputs/GDPS_20251229T12Z
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIR = ROOT / "outputs"

st.title("GDPS 4-Panel Viewer")

base_dir = st.text_input("Image folder", value=str(DEFAULT_DIR))
base_dir = Path(base_dir)

if not base_dir.exists():
    st.error("Folder not found.")
    st.stop()

# Find all pngs recursively
pngs = sorted(base_dir.rglob("*.png"))

# Filter pattern like: GDPS_YYYYMMDDT12Z_F036_4panel.png
pat = re.compile(r".*GDPS_(\d{8})T(\d{2})Z_F(\d{3})_4panel\.png$", re.IGNORECASE)

items = []
for p in pngs:
    m = pat.match(p.name)
    if m:
        ymd, hh, fh = m.group(1), m.group(2), int(m.group(3))
        items.append((ymd, hh, fh, p))

if not items:
    st.warning("No matching GDPS_*_F***_4panel.png found in this folder.")
    st.stop()

# UI controls
ymds = sorted(set(i[0] for i in items))
sel_ymd = st.selectbox("Init date (YYYYMMDD)", ymds, index=len(ymds)-1)

hhs = sorted(set(i[1] for i in items if i[0] == sel_ymd))
sel_hh = st.selectbox("Run (HHZ)", hhs)

fhs = sorted(set(i[2] for i in items if i[0] == sel_ymd and i[1] == sel_hh))
min_fh, max_fh = min(fhs), max(fhs)

sel_fh = st.slider("Forecast hour", min_value=min_fh, max_value=max_fh, value=min_fh, step=12)

# Buttons
c1, c2, c3, c4 = st.columns([1,1,1,3])
with c1:
    if st.button("◀ Prev"):
        sel_fh = max(min_fh, sel_fh - 12)
with c2:
    if st.button("Next ▶"):
        sel_fh = min(max_fh, sel_fh + 12)
with c3:
    if st.button("⏮ F000"):
        sel_fh = min_fh

# Find image
match = [p for (ymd, hh, fh, p) in items if ymd == sel_ymd and hh == sel_hh and fh == sel_fh]
if not match:
    st.error("No image for that selection.")
    st.stop()

img_path = match[0]
st.caption(str(img_path))

img = Image.open(img_path)
st.image(img, use_container_width=False)
st.set_page_config(layout="wide")

# img = Image.open(img_path)
# w, h = img.size

# zoom = st.slider("Zoom", 0.5, 2.5, 1.0, 0.1)
# img2 = img.resize((int(w*zoom), int(h*zoom)), Image.Resampling.LANCZOS)

# st.image(img2)
