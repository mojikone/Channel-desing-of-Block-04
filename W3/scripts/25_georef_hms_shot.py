"""Step 25 - georeference the engineer's HEC-HMS screenshot (Data/images/HMS model.png) so it can sit in a map layout.

HMS draws the terrain without rotation and with equal x/y scaling, so the transform has one scale and one offset:
  * the scale comes from the terrain's full east-west extent, which the screenshot shows complete (white margins left
    and right), while the top and bottom are cut by the HMS window;
  * the vertical offset is found by matching the western silhouette of the shaded terrain (leftmost shaded pixel per
    row) against the western edge of the terrain raster's valid data, row by row, with a least-squares search; the
    eastern silhouette is used as the check.
Output: maps/data/hms_model_georef.tif (RGB, EPSG:32640) and maps/data/hms_georef_check.png (reaches overlaid).
"""
import sys
from pathlib import Path
import numpy as np, rasterio
from rasterio.transform import from_origin
from rasterio.enums import Resampling
from PIL import Image
import scipy.ndimage as ndi
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import HMS, CB04, W3, CRS

SHOT = CB04 / "Data" / "images" / "HMS model.png"; OUT = W3 / "maps" / "data" / "hms_model_georef.tif"
# --- terrain valid mask at ~100 m
src = rasterio.open(HMS / "terrain" / "NSA_5m_B04_Res10m" / "00" / "elevation.tif")
sc = 10; h, w = src.height // sc, src.width // sc; z = src.read(1, out_shape=(h, w), resampling=Resampling.nearest).astype("float64")
nod = src.nodata; valid = ~((z == nod) | (z > 1e30) | (z < -1e4) | np.isnan(z) | (z == 0))
tr = src.transform * src.transform.scale(src.width / w, src.height / h); px = tr.a
print("valid fraction of the raster rectangle:", round(valid.mean(), 3))
rows_v = np.where(valid.any(1))[0]; cols_v = np.where(valid.any(0))[0]
xmin_m = tr.c + cols_v[0] * px; xmax_m = tr.c + (cols_v[-1] + 1) * px; ytop_m = tr.f - rows_v[0] * px; ybot_m = tr.f - (rows_v[-1] + 1) * px
left_m = np.full(h, np.nan); right_m = np.full(h, np.nan)
for r in range(h):
    c = np.where(valid[r])[0]
    if len(c): left_m[r] = tr.c + c[0] * px; right_m[r] = tr.c + (c[-1] + 1) * px
ys_m = tr.f - (np.arange(h) + 0.5) * px
# --- screenshot shaded mask (largest component after opening, so icons and labels outside the terrain are dropped)
im = np.array(Image.open(SHOT).convert("RGB")); nonwhite = im.astype(int).sum(2) < 735
op = ndi.binary_opening(nonwhite, structure=np.ones((9, 9))); lab, n = ndi.label(op); sizes = ndi.sum(op, lab, range(1, n + 1)); big = lab == (np.argmax(sizes) + 1)
big = ndi.binary_fill_holes(big)
rr = np.where(big.any(1))[0]; cc = np.where(big.any(0))[0]
left_p = np.full(im.shape[0], np.nan); right_p = np.full(im.shape[0], np.nan)
for r in range(im.shape[0]):
    c = np.where(big[r])[0]
    if len(c): left_p[r] = c[0]; right_p[r] = c[-1] + 1
s = (xmax_m - xmin_m) / (cc[-1] + 1 - cc[0]); x0 = xmin_m - cc[0] * s          # metres per pixel; map x of pixel column 0
print(f"scale {s:.2f} m/px from the east-west extent ({(xmax_m - xmin_m) / 1000:.1f} km over {cc[-1] + 1 - cc[0]} px)")
# --- vertical offset: map y of pixel row 0 (top edge), searched so the western silhouettes agree
def cost(ytop):
    y_rows = ytop - (np.arange(im.shape[0]) + 0.5) * s                      # map y of each pixel row centre
    lm = np.interp(y_rows, ys_m[::-1], left_m[::-1]); rm = np.interp(y_rows, ys_m[::-1], right_m[::-1])
    lp = x0 + left_p * s; rp = x0 + right_p * s
    ok = np.isfinite(lm) & np.isfinite(lp) & np.isfinite(rm) & np.isfinite(rp)
    ok[:8] = False; ok[-8:] = False                                           # rows cut by the window edge
    return np.nanmean(np.abs(lm[ok] - lp[ok])) + 0.5 * np.nanmean(np.abs(rm[ok] - rp[ok]))
cands = np.arange(ytop_m - 15000, ytop_m + 15000, 50.0); costs = [cost(c) for c in cands]; ytop = float(cands[int(np.argmin(costs))])
fine = np.arange(ytop - 60, ytop + 60, 2.0); costs2 = [cost(c) for c in fine]; ytop = float(fine[int(np.argmin(costs2))])
print(f"top edge y = {ytop:.0f} (raster top {ytop_m:.0f}); silhouette misfit {min(costs2):.0f} m; window shows {im.shape[0] * s / 1000:.1f} of {(ytop_m - ybot_m) / 1000:.1f} km north-south")
# --- write the GeoTIFF
meta = dict(driver="GTiff", height=im.shape[0], width=im.shape[1], count=3, dtype="uint8", crs=CRS, transform=from_origin(x0, ytop, s, s), compress="lzw", photometric="RGB")
with rasterio.open(OUT, "w", **meta) as dst:
    for b in range(3): dst.write(im[:, :, b], b + 1)
print("written", OUT)
# --- check figure: the Basin 3 reaches and the dam axes over the georeferenced image
import geopandas as gpd, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
rch = gpd.read_file(W3 / "elements" / "shp" / "B3" / "Reaches_B3.shp"); ax_ = gpd.read_file(CB04 / "inputs" / "dams" / "Dams updated.shp")
fig, ax = plt.subplots(figsize=(12, 9.3)); ax.imshow(im, extent=(x0, x0 + im.shape[1] * s, ytop - im.shape[0] * s, ytop))
rch.plot(ax=ax, color="red", linewidth=0.6); ax_.plot(ax=ax, color="magenta", linewidth=2); ax.set_title("georeference check: Basin 3 reaches (red) and dam axes (magenta) over the screenshot")
fig.savefig(W3 / "maps" / "data" / "hms_georef_check.png", dpi=110, bbox_inches="tight"); print("check figure written")
