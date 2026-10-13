"""Step 72 (W7) - dyke heights, quantities and cost (engineer, 2026-10-12: "since we have dams upstream the flow depth at the dykes
won't increase much; check the 200-yr depth along the dyke, take an average, add a margin, plus 0.6 m freeboard").
  * depth: the 200-yr flood depth of the plain without the scheme (the clip W3/maps/data/depth_200yr_plain.tif, 5 m) sampled in
    a 25 m band along each dyke of the alignment shapefile (Block 4, class ending in " D"); wet cells = depth > 0.05 m;
  * height H = mean wet depth + MARGIN (0.5 m) + freeboard 0.6 m, rounded up to 0.1 m, floor 1.0 m; the 90th percentile and the
    maximum are reported beside it;
  * quantities per m of dyke from the typical fill section of the project (crest 4.0 m, slopes 1:1.5 both sides, riprap 525 mm
    on the wet face over geotextile, 200 mm gravel on the dry face, 0.4 m strip under the footprint, a 0.5 m toe ditch):
    footprint = 4 + 3H + 3 (m); clearing = footprint; excavation (strip) = 0.4 x footprint; fill = H(4 + 1.5H) + 0.4 x footprint;
    riprap = 0.525 x 1.803H (wet face) + 0.2 x 1.803H (dry-face gravel, priced as riprap) -- the Block 6 cost sheet reproduced to
    within a few percent on its 50 dykes;
  * cost: 0.3 OMR/m2 clearing, 2.1 OMR/m3 excavation, 4 OMR/m3 fill, 13.2 OMR/m3 riprap (the Block 6 rates).
Writes W7/dykes/dykes.csv, dykes.gpkg (lines with the height and cost), dykes.md.
    python 72_dykes.py [--margin 0.5]"""
import os, sys, math, re, numpy as np, pandas as pd, geopandas as gpd, rasterio
from rasterio.mask import mask
HERE = os.path.dirname(os.path.abspath(__file__)); W7 = os.path.dirname(HERE); CB = os.path.dirname(W7); B4 = os.path.dirname(CB)
A = sys.argv[1:]
def opt(k, d=None): return A[A.index(k) + 1] if k in A else d
MARGIN = float(opt("--margin", 0.5)); FREEBOARD = 0.6; BAND = 25.0
OUT = os.path.join(W7, "dykes"); os.makedirs(OUT, exist_ok=True)
g = gpd.read_file(os.path.join(B4, "Hydrology", "SHP", "temp", "Channels and Dykes 04102026.shp")); d = g[(g["Block"] == 4) & g["CHtt"].str.endswith(" D")].copy()
r = rasterio.open(os.path.join(CB, "W3", "maps", "data", "depth_200yr_plain.tif"))
rows = []
for _, f in d.iterrows():
    arr, _ = mask(r, [f.geometry.buffer(BAND)], crop=True, nodata=-9999.0); a = arr[0]; a = a[a > -9000]; wet = a[a > 0.05]
    mean = float(wet.mean()) if len(wet) else 0.0; p90 = float(np.percentile(wet, 90)) if len(wet) else 0.0; mx = float(a.max()) if len(a) else 0.0
    H = max(math.ceil((mean + MARGIN + FREEBOARD) * 10 - 1e-9) / 10, 1.0); L = f.geometry.length
    foot = 4 + 3 * H + 3; clearing = foot * L; excavation = 0.4 * foot * L; fill = (H * (4 + 1.5 * H) + 0.4 * foot) * L; riprap = (0.525 + 0.2) * 1.803 * H * L
    cost = 0.3 * clearing + 2.1 * excavation + 4 * fill + 13.2 * riprap
    rows.append(dict(name=f["Name"], cls=f["CHtt"], L_m=round(L, 1), wet_pct=round(100 * len(wet) / max(len(a), 1)), depth_mean=round(mean, 2), depth_p90=round(p90, 2), depth_max=round(mx, 2), H_m=H,
                     clearing_m2=round(clearing), excavation_m3=round(excavation), fill_m3=round(fill), riprap_m3=round(riprap), cost_OMR=round(cost), cost_mOMR=round(cost / 1e6, 3), geometry=f.geometry))
df = gpd.GeoDataFrame(rows, crs=d.crs)
def key(n):
    m = re.match(r"^(HAW|SHA|SAR|SAK)-D(\d+)", n); return ({"HAW": 0, "SHA": 1, "SAR": 2, "SAK": 3}[m.group(1)], int(m.group(2))) if m else (9, 0)
df["k"] = df.name.map(key); df = df.sort_values("k").drop(columns="k").reset_index(drop=True); df.insert(0, "id", range(1, len(df) + 1))
df.drop(columns="geometry").to_csv(os.path.join(OUT, "dykes.csv"), index=False)
gp = os.path.join(OUT, "dykes.gpkg")
if os.path.exists(gp): os.remove(gp)
df.to_file(gp, layer="dykes", driver="GPKG")
CL = {"FP D": "Flood protection", "Sw M D": "Stormwater main", "Sw S D": "Stormwater secondary"}
md = ["# Dykes: 200-yr depth along the line, adopted height, quantities and cost (margin %.1f m, freeboard %.1f m)" % (MARGIN, FREEBOARD), "",
      "| id | dyke | class | length m | depth mean / p90 / max | height m | clearing m2 | excavation m3 | fill m3 | riprap m3 | cost mOMR |", "|---|---|---|---|---|---|---|---|---|---|---|"]
for _, x in df.iterrows(): md.append("| %d | %s | %s | %.0f | %.2f / %.2f / %.2f | %.1f | %d | %d | %d | %d | %.3f |" % (x.id, x["name"], CL.get(x.cls, x.cls), x.L_m, x.depth_mean, x.depth_p90, x.depth_max, x.H_m, x.clearing_m2, x.excavation_m3, x.fill_m3, x.riprap_m3, x.cost_mOMR))
md += ["", "total: %d dykes, %.1f km, heights %.1f to %.1f m, fill %.0f m3, cost %.2f mOMR" % (len(df), df.L_m.sum() / 1000, df.H_m.min(), df.H_m.max(), df.fill_m3.sum(), df.cost_OMR.sum() / 1e6)]
open(os.path.join(OUT, "dykes.md"), "w", encoding="utf-8").write("\n".join(md)); print("\n".join(md[-1:])); print(df[["id", "name", "cls", "L_m", "depth_mean", "depth_p90", "H_m", "cost_mOMR"]].to_string(index=False))
