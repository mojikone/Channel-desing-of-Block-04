"""Step 73 (W9, engineer 2026-10-14) - the channel terrain on the ground that made the Civil 3D surfaces: the 0.5 m project DEM
(the W4 source), not the 5 m block model of W7. The engineer's Channel Terrain tool (used as a module, never edited) stamps the
designed sections of every reach (R9, 200-year) at RES m; the cut and fill are measured against the 0.5 m DEM warped onto the
channel grid. Then everything merged: W9/terrain/Block04_channel_surfaces_2m.tif (the designed surfaces of the 37 channels,
lowest where they meet) and W9/terrain/Block04_terrain_with_channels_2m.tif (the 0.5 m ground resampled to 2 m over the
channel corridors with the channels cut in; nothing outside the corridors). Quantities as W7 step 73 -> W9/volumes/.
    python 73_terrain_w9.py [--run run_20261012_1758] [--res 2] [--channels A,B] [--skip-done] [--merge-only]"""
import os, sys, json, math, re, time, importlib.util, io, contextlib
from pathlib import Path
import numpy as np, pandas as pd, geopandas as gpd, rasterio
from rasterio.warp import reproject, Resampling
from rasterio.merge import merge as rio_merge
from rasterio.transform import from_origin
HERE = os.path.dirname(os.path.abspath(__file__)); W9 = os.path.dirname(HERE); CB = os.path.dirname(W9); B4 = os.path.dirname(CB); W7 = os.path.join(CB, "W7")
A = sys.argv[1:]
def opt(k, d=None): return A[A.index(k) + 1] if k in A else d
RUN = opt("--run", "run_20261012_1758"); RES = float(opt("--res", 2)); ONLY = opt("--channels"); SKIP = "--skip-done" in A; MERGE_ONLY = "--merge-only" in A
TOOL = r"C:\Users\mojtaba\Documents\Channel Terrain\W6\scripts\channel_terrain.py"
_LOCAL = os.path.join(B4, "Hydraulic", "Terrain", "GGC_4_MERGE_HDSM.tif")   # his local copy of the 0.5 m DEM (2026-10-14)
DEM = _LOCAL if os.path.exists(_LOCAL) else "//FILESERVER-/Works/2224 Flood Protection Scheme in North & South Batinah_MAFWWR/10-DATABASE/01 DEM/Prosessed_DEM/OUTPUT/GGC4_DTM_GMAP_NSA.tif"   # the 0.5 m DEM of W4 (read only)
print("ground DEM:", DEM)
ND_LIMIT = 1e30
LANDUSE = "W:/2224 Flood Protection Scheme in North & South Batinah_MAFWWR/06-WORKING/13-Study and Design/01-FS and PD/00-General/02-Land Use/ALL_MOH_CLEANED/LandUSE_block4.shp"
OUT = os.path.join(W9, "volumes"); TER = os.path.join(W9, "terrain"); os.makedirs(OUT, exist_ok=True); os.makedirs(TER, exist_ok=True)
RATE = dict(exc=2.1, fill=4.0, riprap=13.2, clear=0.3); RIPRAP_T = 0.3; EXTRA = 15.5; GROUND_BUF = 100.0
exp = pd.read_csv(os.path.join(W7, "sewergems", "results", RUN, "bridge_exports", "conduits_200yr.csv")).set_index("label")
seg = gpd.read_file(os.path.join(W7, "final", "Block4_design_segments.shp"))
seg = seg.merge(exp[["start_inv", "stop_inv", "slope", "rise_m", "span_m", "flow"]], left_on="SGLabel", right_index=True, how="left")
def order(n):
    m = re.match(r"^(HAW|SHA|SAR|SAK)-CH(\d+)", n); return ({"HAW": 0, "SHA": 1, "SAR": 2, "SAK": 3}[m.group(1)], int(m.group(2))) if m else (9, 0)
channels = sorted(seg.Channel.unique(), key=order)
if ONLY: channels = [c for c in channels if c in ONLY.split(",")]

def ground_on(grid_transform, shape, crs):
    """The 0.5 m DEM warped (bilinear) onto a channel grid; the DEM's 3.4e38 nodata -> nan."""
    g = np.full(shape, np.nan, dtype="float64")
    with rasterio.open(DEM) as src:
        reproject(rasterio.band(src, 1), g, dst_transform=grid_transform, dst_crs=crs, resampling=Resampling.bilinear, dst_nodata=np.nan, src_nodata=src.nodata)
    g[~np.isfinite(g) | (np.abs(g) > ND_LIMIT)] = np.nan; return g

if not MERGE_ONLY:
    spec = importlib.util.spec_from_file_location("channel_terrain", TOOL); ct = importlib.util.module_from_spec(spec); spec.loader.exec_module(ct)
    lu = None
    try: lu = gpd.read_file(LANDUSE).to_crs("EPSG:32640")[["ParcelLand", "geometry"]]
    except Exception as e: print("land use layer not read:", e)
    rows = []
    for ch in channels:
        t0 = time.time(); d = os.path.join(OUT, ch); os.makedirs(d, exist_ok=True); vj = os.path.join(d, "volumes.json")
        s = seg[seg.Channel == ch].copy()
        if SKIP and os.path.exists(vj) and os.path.exists(os.path.join(d, "ground_2m.tif")): rows.append(json.load(open(vj))); print(ch, "(kept)"); continue
        g = gpd.GeoDataFrame({"LABEL": s.SGLabel, "SPAN": s.span_m.astype(float), "RISE": s.rise_m.astype(float), "INV_STRT": s.start_inv.astype(float), "INV_STP": s.stop_inv.astype(float), "S": s.slope.astype(float), "START_NODE": s.SGFrom, "STOP_NOD2": s.SGTo}, geometry=s.geometry, crs=s.crs)
        shp = os.path.join(d, "reaches.shp"); g.to_file(shp)
        ct.SHAPEFILE = Path(shp); ct.DEM_PATH = Path(DEM); ct.OUTPUT_DIR = Path(d); ct.OUTPUT_PATH = Path(d) / "channel_terrain.tif"; ct.MMAP_PATH = Path(d) / "_work_array.dat"; ct.RESOLUTION = RES
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf): ct.main()
        open(os.path.join(d, "tool.log"), "w", encoding="utf-8").write(buf.getvalue())
        try: os.remove(os.path.join(d, "_work_array.dat"))
        except Exception: pass
        with rasterio.open(os.path.join(d, "channel_terrain.tif")) as r:
            des = r.read(1).astype("float64"); nod = r.nodata if r.nodata is not None else -9999.0; tr = r.transform; crs = r.crs; shape = des.shape
        dem = ground_on(tr, shape, crs)
        with rasterio.open(os.path.join(d, "ground_2m.tif"), "w", driver="GTiff", height=shape[0], width=shape[1], count=1, dtype="float32", crs=crs, transform=tr, nodata=-9999.0, compress="lzw") as w:
            w.write(np.where(np.isfinite(dem), dem, -9999.0).astype("float32"), 1)
        m = (des != nod) & np.isfinite(des) & np.isfinite(dem); cell = abs(tr.a * tr.e)
        diff = np.where(m, dem - des, 0.0); cut = float(diff[diff > 0].sum() * cell); fill = float((-diff[diff < 0]).sum() * cell); foot = float(m.sum() * cell)
        nground = int(((des != nod) & ~np.isfinite(dem)).sum())
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
                   corridor_ha=round(float(corr.area) / 1e4, 2), land_take_ha=take, cost_OMR=round(cost), cost_mOMR=round(cost / 1e6, 3), res_m=RES, ground="0.5 m project DEM", cells_without_ground=nground, seconds=round(time.time() - t0))
        json.dump(row, open(vj, "w"), indent=1); rows.append(row)
        print("%-12s %2d reaches %7.0f m  cut %10.0f  fill %9.0f  footprint %9.0f m2  corridor %6.1f ha  cost %6.2f mOMR  no-ground cells %d  (%d s)" % (ch, len(s), L, cut, fill, foot, corr.area / 1e4, cost / 1e6, nground, time.time() - t0), flush=True)
    df = pd.DataFrame(rows); df.to_csv(os.path.join(OUT, "channel_quantities.csv"), index=False)
    md = ["# Channel quantities and cost, 200-yr design %s, terrain tool at %.0f m on the 0.5 m project DEM" % (RUN, RES), "", "| channel | class | length km | cut m3 | fill m3 | clearing m2 | riprap m2 | corridor ha | cost mOMR |", "|---|---|---|---|---|---|---|---|---|"]
    for _, x in df.iterrows(): md.append("| %s | %s | %.1f | %d | %d | %d | %d | %.1f | %.2f |" % (x.channel, x.cls, x.length_m / 1000, x.cut_m3, x.fill_m3, x.footprint_m2, x.protection_m2, x.corridor_ha, x.cost_mOMR))
    md += ["", "total: %d channels, %.1f km, cut %.0f m3, fill %.0f m3, clearing %.0f m2, riprap %.0f m2, cost %.1f mOMR" % (len(df), df.length_m.sum() / 1000, df.cut_m3.sum(), df.fill_m3.sum(), df.footprint_m2.sum(), df.protection_m2.sum(), df.cost_OMR.sum() / 1e6)]
    open(os.path.join(OUT, "channel_quantities.md"), "w", encoding="utf-8").write("\n".join(md)); print(md[-1])

# ---- the merged rasters
chs = sorted(seg.Channel.unique(), key=order)
surf = [rasterio.open(os.path.join(OUT, c, "channel_terrain.tif")) for c in chs if os.path.exists(os.path.join(OUT, c, "channel_terrain.tif"))]
grd = [rasterio.open(os.path.join(OUT, c, "ground_2m.tif")) for c in chs if os.path.exists(os.path.join(OUT, c, "ground_2m.tif"))]
print("merging", len(surf), "channel surfaces and", len(grd), "ground tiles")
msurf, tr = rio_merge(surf, nodata=-9999.0, method="min", res=(RES, RES)); msurf = msurf[0]
for r in surf: r.close()
prof = dict(driver="GTiff", height=msurf.shape[0], width=msurf.shape[1], count=1, dtype="float32", crs="EPSG:32640", transform=tr, nodata=-9999.0, compress="lzw", tiled=True, BIGTIFF="IF_SAFER")
with rasterio.open(os.path.join(TER, "Block04_channel_surfaces_2m.tif"), "w", **prof) as w: w.write(msurf.astype("float32"), 1)
mgrd = np.full(msurf.shape, -9999.0, dtype="float32")
for r in grd:
    tmp = np.full(msurf.shape, np.nan, dtype="float64"); reproject(rasterio.band(r, 1), tmp, dst_transform=tr, dst_crs="EPSG:32640", resampling=Resampling.nearest, dst_nodata=np.nan, src_nodata=-9999.0)
    ok = np.isfinite(tmp) & (mgrd == -9999.0); mgrd[ok] = tmp[ok]; r.close()
# the corridor mask: bed + 15.5 m + GROUND_BUF around every reach
corr = gpd.GeoSeries([ln.buffer(sp / 2 + EXTRA + GROUND_BUF, cap_style=2) for ln, sp in zip(seg.geometry, seg.span_m.astype(float))], crs=seg.crs).union_all()
from rasterio.features import geometry_mask
inside = ~geometry_mask([corr], out_shape=msurf.shape, transform=tr, invert=False)
full = np.where(msurf != -9999.0, msurf, mgrd); full[~inside] = -9999.0
with rasterio.open(os.path.join(TER, "Block04_terrain_with_channels_2m.tif"), "w", **prof) as w: w.write(full.astype("float32"), 1)
open(os.path.join(TER, "README.txt"), "w", encoding="utf-8").write(
    "Block 04 channel terrain (200-year design), 2 m cells, EPSG:32640.\n"
    "Block04_channel_surfaces_2m.tif: the designed channel surfaces (bed and side slopes) of the 37 channels, the lowest surface where channels meet; nodata elsewhere.\n"
    "Block04_terrain_with_channels_2m.tif: the ground of the 0.5 m project terrain model resampled to 2 m over the channel corridors (bed, embankments, access roads and 100 m around), with the designed channels cut in; nodata outside.\n"
    "Per channel: volumes/<channel>/channel_terrain.tif (designed surface) and ground_2m.tif (the 0.5 m ground on the same grid).\n")
print("merged rasters:", msurf.shape, "->", TER)
