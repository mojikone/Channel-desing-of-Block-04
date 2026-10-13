"""Step 73 (W7) - channel earthworks, protection and land take, channel by channel, with the engineer's Channel Terrain tool
(C:/Users/mojtaba/Documents/Channel Terrain/W6/scripts/channel_terrain.py, used as a module, never edited): it stamps the designed
channel surface (flat bed at the invert, 1:1.5 walls, cut daylighting at 1:1.5 or a 4 m crest embankment in fill) into a raster
from the reach polylines and the existing ground, here the 5 m DEM of the block at RESOLUTION m. Volumes = the difference between
the DEM (bilinear at the output cells) and the designed surface over the footprint: cut where the ground is above, fill where it
is below. Protection = the two side slopes of every reach (1.803 x depth, both sides, over its length; the project's riprap, as in
the Block 6 estimate). Clearing = the footprint. Land take = the corridor (bed + 15.5 m each side, the plan outline of the
drawings) by land-use class of the cadastre layer. Cost = the Block 6 rates (2.1 excavation, 4 fill, 13.2 riprap on 0.3 m,
0.3 clearing, OMR). Inputs: W7/final/Block4_design_segments.shp with the sizes and inverts of the run named in --run (200 yr).
Writes W7/volumes/<channel>/ (reaches.shp, channel_terrain.tif, volumes.json) and W7/volumes/channel_quantities.csv + .md.
    python 73_channel_volumes.py [--run run_20261012_1758] [--res 2] [--channels HAW-CH1-FP,...] [--skip-done]"""
import os, sys, json, math, re, time, importlib.util, shutil
from pathlib import Path
import numpy as np, pandas as pd, geopandas as gpd, rasterio
from rasterio.warp import reproject, Resampling
HERE = os.path.dirname(os.path.abspath(__file__)); W7 = os.path.dirname(HERE); CB = os.path.dirname(W7); B4 = os.path.dirname(CB)
A = sys.argv[1:]
def opt(k, d=None): return A[A.index(k) + 1] if k in A else d
RUN = opt("--run", "run_20261012_1758"); RES = float(opt("--res", 2)); ONLY = opt("--channels"); SKIP = "--skip-done" in A
TOOL = r"C:\Users\mojtaba\Documents\Channel Terrain\W6\scripts\channel_terrain.py"
DEM = os.path.join(B4, "Hydrology", "Terrain", "NSA_Batinah_5m_Block_04.tif")
LANDUSE = "W:/2224 Flood Protection Scheme in North & South Batinah_MAFWWR/06-WORKING/13-Study and Design/01-FS and PD/00-General/02-Land Use/ALL_MOH_CLEANED/LandUSE_block4.shp"
OUT = os.path.join(W7, "volumes"); os.makedirs(OUT, exist_ok=True)
RATE = dict(exc=2.1, fill=4.0, riprap=13.2, clear=0.3); RIPRAP_T = 0.3; EXTRA = 15.5
spec = importlib.util.spec_from_file_location("channel_terrain", TOOL); ct = importlib.util.module_from_spec(spec); spec.loader.exec_module(ct)
exp = pd.read_csv(os.path.join(W7, "sewergems", "results", RUN, "bridge_exports", "conduits_200yr.csv")).set_index("label")
seg = gpd.read_file(os.path.join(W7, "final", "Block4_design_segments.shp"))
seg = seg.merge(exp[["start_inv", "stop_inv", "slope", "rise_m", "span_m", "flow"]], left_on="SGLabel", right_index=True, how="left")
lu = None
try: lu = gpd.read_file(LANDUSE).to_crs("EPSG:32640")[["ParcelLand", "geometry"]]
except Exception as e: print("land use layer not read:", e)
def order(n):
    m = re.match(r"^(HAW|SHA|SAR|SAK)-CH(\d+)", n); return ({"HAW": 0, "SHA": 1, "SAR": 2, "SAK": 3}[m.group(1)], int(m.group(2))) if m else (9, 0)
channels = sorted(seg.Channel.unique(), key=order)
if ONLY: channels = [c for c in channels if c in ONLY.split(",")]
rows = []
for ch in channels:
    t0 = time.time(); d = os.path.join(OUT, ch); os.makedirs(d, exist_ok=True); vj = os.path.join(d, "volumes.json")
    s = seg[seg.Channel == ch].copy()
    if SKIP and os.path.exists(vj): rows.append(json.load(open(vj))); print(ch, "(kept)"); continue
    g = gpd.GeoDataFrame({"LABEL": s.SGLabel, "SPAN": s.span_m.astype(float), "RISE": s.rise_m.astype(float), "INV_STRT": s.start_inv.astype(float), "INV_STP": s.stop_inv.astype(float), "S": s.slope.astype(float), "START_NODE": s.SGFrom, "STOP_NOD2": s.SGTo}, geometry=s.geometry, crs=s.crs)   # the tool reads START_NODE / STOP_NOD2
    shp = os.path.join(d, "reaches.shp"); g.to_file(shp)
    ct.SHAPEFILE = Path(shp); ct.DEM_PATH = Path(DEM); ct.OUTPUT_DIR = Path(d); ct.OUTPUT_PATH = Path(d) / "channel_terrain.tif"; ct.MMAP_PATH = Path(d) / "_work_array.dat"; ct.RESOLUTION = RES
    import io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf): ct.main()
    open(os.path.join(d, "tool.log"), "w", encoding="utf-8").write(buf.getvalue())
    try: os.remove(os.path.join(d, "_work_array.dat"))
    except Exception: pass
    with rasterio.open(os.path.join(d, "channel_terrain.tif")) as r:
        des = r.read(1).astype("float64"); nod = r.nodata if r.nodata is not None else -9999.0; tr = r.transform; crs = r.crs; shape = des.shape
    dem = np.full(shape, np.nan, dtype="float64")
    with rasterio.open(DEM) as src:
        reproject(rasterio.band(src, 1), dem, dst_transform=tr, dst_crs=crs, resampling=Resampling.bilinear, dst_nodata=np.nan)
    m = (des != nod) & np.isfinite(des) & np.isfinite(dem); cell = abs(tr.a * tr.e)
    diff = np.where(m, dem - des, 0.0); cut = float(diff[diff > 0].sum() * cell); fill = float((-diff[diff < 0]).sum() * cell); foot = float(m.sum() * cell)
    del des, dem, diff
    L = float(s.Length.sum()); prot = float((2 * 1.803 * s.rise_m * s.Length).sum())
    corr = gpd.GeoSeries([ln.buffer(sp / 2 + EXTRA, cap_style=2) for ln, sp in zip(s.geometry, s.span_m.astype(float))], crs=s.crs).union_all()
    take = {}
    if lu is not None:
        inter = lu[lu.intersects(corr)].copy()
        if len(inter):
            inter["a"] = inter.geometry.intersection(corr).area / 1e4
            take = {str(k): round(float(v), 2) for k, v in inter.groupby("ParcelLand")["a"].sum().items() if v > 0.005}
    cost = RATE["exc"] * cut + RATE["fill"] * fill + RATE["riprap"] * prot * RIPRAP_T + RATE["clear"] * foot
    row = dict(channel=ch, cls=s.Class.iloc[0], reaches=len(s), length_m=round(L, 1), span_min=float(s.span_m.min()), span_max=float(s.span_m.max()), cut_m3=round(cut), fill_m3=round(fill), footprint_m2=round(foot), protection_m2=round(prot),
               corridor_ha=round(float(corr.area) / 1e4, 2), land_take_ha=take, cost_OMR=round(cost), cost_mOMR=round(cost / 1e6, 3), res_m=RES, seconds=round(time.time() - t0))
    json.dump(row, open(vj, "w"), indent=1); rows.append(row)
    print("%-12s %2d reaches %7.0f m  cut %10.0f  fill %9.0f  footprint %9.0f m2  protection %8.0f m2  corridor %6.1f ha  cost %6.2f mOMR  (%d s)" % (ch, len(s), L, cut, fill, foot, prot, corr.area / 1e4, cost / 1e6, time.time() - t0), flush=True)
df = pd.DataFrame(rows); df.to_csv(os.path.join(OUT, "channel_quantities.csv"), index=False)
md = ["# Channel quantities and cost, 200-yr design %s, terrain tool at %.0f m on the 5 m DEM" % (RUN, RES), "", "| channel | class | length km | cut m3 | fill m3 | clearing m2 | riprap m2 | corridor ha | cost mOMR |", "|---|---|---|---|---|---|---|---|---|"]
for _, x in df.iterrows(): md.append("| %s | %s | %.1f | %d | %d | %d | %d | %.1f | %.2f |" % (x.channel, x.cls, x.length_m / 1000, x.cut_m3, x.fill_m3, x.footprint_m2, x.protection_m2, x.corridor_ha, x.cost_mOMR))
md += ["", "total: %d channels, %.1f km, cut %.0f m3, fill %.0f m3, clearing %.0f m2, riprap %.0f m2, cost %.1f mOMR" % (len(df), df.length_m.sum() / 1000, df.cut_m3.sum(), df.fill_m3.sum(), df.footprint_m2.sum(), df.protection_m2.sum(), df.cost_OMR.sum() / 1e6)]
open(os.path.join(OUT, "channel_quantities.md"), "w", encoding="utf-8").write("\n".join(md)); print(md[-1])
